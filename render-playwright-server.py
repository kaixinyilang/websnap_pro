"""
WebSnap Pro — Playwright 专业截图引擎（部署到 Render / Railway）
支持交互式滑块验证：检测到验证页 → 返回截图让用户手动操作 → 继续截图

部署：render.com → Build: pip install -r requirements-playwright.txt
                    Start: python -m playwright install chromium && python render-playwright-server.py
"""

import os, re, sys, asyncio, tempfile, uuid, time, traceback
from pathlib import Path
from io import BytesIO
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import Response
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("Missing: pip install fastapi uvicorn pydantic")
    sys.exit(1)

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Missing: pip install playwright")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Missing: pip install pillow")
    sys.exit(1)

try:
    from reportlab.lib.pagesizes import A4, A3
    from reportlab.pdfgen import canvas as rc
except ImportError:
    print("Missing: pip install reportlab")
    sys.exit(1)

# ══════════════════════════════════════════════════════════
app = FastAPI(title="WebSnap Pro — Playwright Engine", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

# ── 会话管理（保持浏览器打开便于交互验证） ──────────────
sessions = {}  # { session_id: { "browser", "page", "ctx", "created_at" } }

def clean_old_sessions():
    now = time.time()
    stale = [sid for sid, s in sessions.items() if now - s["created_at"] > 300]
    for sid in stale:
        try:
            asyncio.create_task(sessions[sid]["browser"].close())
        except:
            pass
        sessions.pop(sid, None)

# ── 请求参数 ─────────────────────────────────────────────
class CaptureRequest(BaseModel):
    url: str = ""
    format: str = "png"
    viewport_width: int = 1280
    scale: int = 2
    wait: int = 3
    quality: int = 90
    pdf_mode: str = "a4"
    session_id: str = ""         # 已有会话 ID（继续操作）
    action: str = ""             # 操作: ""空=截图 / "drag"拖拽 / "click"点击 / "finish"完成
    start_x: int = 0
    start_y: int = 0
    end_x: int = 0
    end_y: int = 0
    click_x: int = 0
    click_y: int = 0

# ── 工具函数 ─────────────────────────────────────────────
def sanitize(url: str) -> str:
    n = re.sub(r"https?://", "", url)
    return re.sub(r"[^\w\-]", "_", n)[:48]

def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw

def is_captcha_page(title, body_text):
    """检测是否为滑块验证/安全验证页面"""
    text = (title + " " + body_text)[:3000].lower()
    keywords = [
        "验证码", "滑块验证", "安全验证", "人机验证", "请完成安全验证",
        "captcha", "verify you are human", "please confirm you are not",
        "just a moment", "checking your browser",
        "access denied", "blocked", "security check",
        "滑动", "请按住滑块", "拖动滑块",
    ]
    return any(kw in text for kw in keywords)

async def find_chromium():
    import glob
    for pat in ["/opt/render/.cache/ms-playwright/**/chrome",
                "/opt/render/.cache/ms-playwright/**/chrome-headless-shell",
                "/opt/render/.cache/ms-playwright/**/chromium"]:
        hits = glob.glob(pat, recursive=True)
        if hits:
            return hits[0]
    for c in ["/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"]:
        if Path(c).exists():
            return c
    return None

CHROMIUM_ARGS = [
    "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage",
    "--disable-gpu", "--disable-blink-features=AutomationControlled",
    "--disable-blink-features=IdleDetection",
    "--disable-client-side-phishing-detection",
    "--disable-component-update", "--disable-background-networking",
    "--disable-sync", "--no-first-run",
]

# ── 图片/PDF 转换 ────────────────────────────────────────

def convert_format(png_bytes, fmt, quality, pdf_mode):
    if fmt == "png":
        return png_bytes, "image/png", ".png"
    img = Image.open(BytesIO(png_bytes)).convert("RGB")
    iw, ih = img.size
    if fmt == "jpg":
        buf = BytesIO()
        img.save(buf, "JPEG", quality=quality, optimize=True)
        return buf.getvalue(), "image/jpeg", ".jpg"
    if fmt == "pdf":
        buf = BytesIO()
        pw, ph = {"a4": A4, "a3": A3}.get(pdf_mode, (iw * 0.75, ih * 0.75))
        c = rc.Canvas(buf, pagesize=(pw, ph))
        if pdf_mode in ("a4", "a3"):
            sx = pw / iw; sh = ih * sx; y = 0
            while y < sh:
                ps = int(y / sx); pe = min(ih, int((y + ph) / sx))
                stripe = img.crop((0, ps, iw, pe))
                sb = BytesIO(); stripe.save(sb, "PNG"); sb.seek(0)
                c.drawImage(sb, 0, ph - (pe - ps) * sx, width=pw, height=(pe - ps) * sx)
                y += ph
                if y < sh: c.showPage()
        else:
            c.drawImage(BytesIO(png_bytes), 0, 0, width=pw, height=ph)
        c.save()
        return buf.getvalue(), "application/pdf", ".pdf"
    return png_bytes, "image/png", ".png"

# ══════════════════════════════════════════════════════════
# API
# ══════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    return {"status": "ok", "engine": "playwright", "sessions": len(sessions),
            "time": datetime.now().isoformat()}


@app.post("/api/capture")
async def capture(req: CaptureRequest):
    url = normalize_url(req.url)
    session_id = req.session_id

    # ── 已有会话：执行操作 ────────────────────────────────
    if session_id and session_id in sessions:
        s = sessions[session_id]
        s["created_at"] = time.time()  # 续期
        page = s["page"]

        try:
            if req.action == "drag":
                # 鼠标拖动（用于滑块验证）
                await page.mouse.move(req.start_x, req.start_y)
                await page.mouse.down()
                steps = 20
                for i in range(steps + 1):
                    x = req.start_x + (req.end_x - req.start_x) * i / steps
                    y = req.start_y + (req.end_y - req.start_y) * i / steps
                    await page.mouse.move(x, y)
                    await asyncio.sleep(0.02)
                await page.mouse.up()
                await asyncio.sleep(2)

            elif req.action == "click":
                await page.mouse.click(req.click_x, req.click_y)
                await asyncio.sleep(2)

            elif req.action == "finish":
                # 用户确认，等待渲染 → 全页截图 → 关闭浏览器
                await asyncio.sleep(req.wait)
                fh = await page.evaluate("document.body.scrollHeight")
                tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                tmp_path = tmp.name; tmp.close()
                await page.screenshot(path=tmp_path, full_page=True, type="png", timeout=120000)
                await s["browser"].close()
                sessions.pop(session_id, None)
                with open(tmp_path, "rb") as f:
                    png_bytes = f.read()
                Path(tmp_path).unlink(missing_ok=True)
                output, ctype, suffix = convert_format(png_bytes, req.format, req.quality, req.pdf_mode)
                slug = sanitize(url)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{slug}_{ts}{suffix}"
                return Response(content=output, media_type=ctype,
                                headers={"Content-Disposition": f'attachment; filename="{filename}"',
                                         "Access-Control-Allow-Origin": "*"})

            # 操作后截图 → 返回给用户判断
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp_path = tmp.name; tmp.close()
            await page.screenshot(path=tmp_path, full_page=False, type="png", timeout=60000)
            with open(tmp_path, "rb") as f:
                png_bytes = f.read()
            Path(tmp_path).unlink(missing_ok=True)

            # 再次检测验证
            title = (await page.title()).lower()
            body_text = (await page.evaluate("() => document.body.innerText")).lower()[:2000]
            still_captcha = is_captcha_page(title, body_text)

            return Response(content=png_bytes, media_type="image/png",
                            headers={"X-Session-Id": session_id,
                                     "X-Captcha-Detected": "true" if still_captcha else "false",
                                     "Access-Control-Expose-Headers": "X-Session-Id, X-Captcha-Detected",
                                     "Access-Control-Allow-Origin": "*"})

        except Exception as e:
            # 会话异常，清理
            try: await s["browser"].close()
            except: pass
            sessions.pop(session_id, None)
            raise HTTPException(status_code=502, detail=f"操作失败: {e}")

    # ── 新会话：启动浏览器 → 访问页面 ─────────────────────
    clean_old_sessions()

    async with async_playwright() as p:
        launch_kwargs = dict(headless=True, timeout=30000, args=CHROMIUM_ARGS)
        exe = await find_chromium()
        if exe:
            launch_kwargs["executable_path"] = exe
        browser = await p.chromium.launch(**launch_kwargs)

        ctx = await browser.new_context(
            viewport={"width": req.viewport_width, "height": 900},
            device_scale_factor=req.scale,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = await ctx.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=45000)
        except Exception:
            try:
                await page.goto(url, wait_until="load", timeout=30000)
            except Exception:
                pass

        await asyncio.sleep(min(req.wait, 2))  # 初始等待

        # ── 检测验证页 ──────────────────────────────────────
        title = (await page.title()).lower()
        body_text = (await page.evaluate("() => document.body.innerText")).lower()[:2000]
        captcha = is_captcha_page(title, body_text)

        # ── 截图 ──
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp_path = tmp.name; tmp.close()
        await page.screenshot(path=tmp_path, full_page=False, type="png", timeout=60000)
        with open(tmp_path, "rb") as f:
            png_bytes = f.read()
        Path(tmp_path).unlink(missing_ok=True)

        if captcha:
            # 创建会话，保持浏览器打开等待用户操作
            sid = str(uuid.uuid4())[:8]
            sessions[sid] = {"browser": browser, "page": page, "ctx": ctx, "created_at": time.time()}
            print(f"[Session] {sid} — captcha detected, waiting for user interaction")

            return Response(content=png_bytes, media_type="image/png",
                            headers={"X-Session-Id": sid,
                                     "X-Captcha-Detected": "true",
                                     "Access-Control-Expose-Headers": "X-Session-Id, X-Captcha-Detected",
                                     "Access-Control-Allow-Origin": "*"})

        # ── 没有验证，直接截图完成 ──
        await asyncio.sleep(max(0, req.wait - 2))
        fh = await page.evaluate("document.body.scrollHeight")
        tmp2 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        t2_path = tmp2.name; tmp2.close()
        await page.screenshot(path=t2_path, full_page=True, type="png", timeout=120000)
        await browser.close()

        with open(t2_path, "rb") as f:
            full_png = f.read()
        Path(t2_path).unlink(missing_ok=True)

        output, ctype, suffix = convert_format(full_png, req.format, req.quality, req.pdf_mode)
        slug = sanitize(url)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{slug}_{ts}{suffix}"
        print(f"[Capture] OK  {len(output)/1024:.0f}KB  →  {filename}")

        return Response(content=output, media_type=ctype,
                        headers={"Content-Disposition": f'attachment; filename="{filename}"',
                                 "Access-Control-Allow-Origin": "*"})


# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 WebSnap Pro Playwright Engine — http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
