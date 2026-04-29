"""
WebSnap Pro — Playwright 专业截图引擎（部署到 Render / Railway）

使用真实 Chromium 浏览器渲染截图，能通过绝大多数反爬验证。
部署到 Render.com 免费版即可运行，无需本地环境。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

部署步骤 / Deploy:

  1. 推送到 GitHub
  2. Render.com → New Web Service → 选择仓库
  3. Build Command（构建命令）:
       pip install -r requirements-playwright.txt
       && python -m playwright install chromium
  4. Start Command（启动命令）:
       python render-playwright-server.py
  5. 部署完成，获得 https://your-app.onrender.com

前端设置：
  打开 WebSnap Pro → 切换"Playwright 引擎" → 填入后端 URL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os, re, sys, asyncio, tempfile, traceback
from pathlib import Path
from io import BytesIO
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import Response
    from pydantic import BaseModel, HttpUrl
    import uvicorn
except ImportError:
    print("缺少依赖 / Missing: pip install fastapi uvicorn pydantic")
    sys.exit(1)

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("缺少依赖 / Missing: pip install playwright && python -m playwright install chromium")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("缺少依赖 / Missing: pip install pillow")
    sys.exit(1)

try:
    from reportlab.lib.pagesizes import A4, A3
    from reportlab.pdfgen import canvas as rc
except ImportError:
    print("缺少依赖 / Missing: pip install reportlab")
    sys.exit(1)


# ══════════════════════════════════════════════════════════
# FastAPI 应用
# ══════════════════════════════════════════════════════════

app = FastAPI(
    title="WebSnap Pro — Playwright Engine",
    description="真实浏览器渲染截图，支持 PNG / JPG / PDF",
    version="2.0.0",
)

# ── CORS（允许 Vercel 前端跨域调用） ─────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 请求参数 ─────────────────────────────────────────────

class CaptureRequest(BaseModel):
    url: str
    format: str = "png"           # png / jpg / pdf
    viewport_width: int = 1280
    scale: int = 2
    wait: int = 3
    quality: int = 90             # JPG quality (10-100)
    pdf_mode: str = "a4"          # a4 / a3 / full


# ── 工具函数 ─────────────────────────────────────────────

def sanitize(url: str) -> str:
    n = re.sub(r"https?://", "", url)
    return re.sub(r"[^\w\-]", "_", n)[:48]

def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw


# ── Chromium 启动 ────────────────────────────────────────

async def find_chromium():
    """在 Render/Railway 环境中查找 Chromium"""
    import glob
    candidates = [
        # Playwright 安装的
        *glob.glob("/home/*/.cache/ms-playwright/chromium-*/chrome-linux*/chrome"),
        *glob.glob("/root/.cache/ms-playwright/chromium-*/chrome-linux*/chrome"),
        *glob.glob("/home/*/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux*/chrome-headless-shell"),
        *glob.glob("/root/.cache/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-linux*/chrome-headless-shell"),
        # 系统安装的
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None

CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-blink-features=AutomationControlled",
    "--disable-blink-features=IdleDetection",
    "--disable-client-side-phishing-detection",
    "--disable-component-update",
    "--disable-background-networking",
    "--disable-sync",
    "--no-first-run",
]


# ── 核心截图函数 ─────────────────────────────────────────

async def capture_async(url, vw, scale, wait):
    """返回 (PNG bytes, page_height)"""
    async with async_playwright() as p:
        # ── 启动浏览器 ──
        launch_kwargs = dict(
            headless=True,
            timeout=30000,
            args=CHROMIUM_ARGS,
        )

        # 自动查找 Chromium 路径
        exe = await find_chromium()
        if exe:
            launch_kwargs["executable_path"] = exe

        # 尝试启动，失败时用 Playwright 自动管理
        try:
            browser = await p.chromium.launch(**launch_kwargs)
        except Exception as e:
            del launch_kwargs["executable_path"]
            browser = await p.chromium.launch(**launch_kwargs)

        # ── 创建上下文 ──
        ctx = await browser.new_context(
            viewport={"width": vw, "height": 900},
            device_scale_factor=scale,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            # 允许所有 cookies 和 localStorage
            no_viewport=False,
        )
        page = await ctx.new_page()

        # ── 加载页面 ──
        try:
            await page.goto(url, wait_until="networkidle", timeout=45000)
        except Exception:
            try:
                await page.goto(url, wait_until="load", timeout=30000)
            except Exception:
                pass  # 继续执行，至少加载了部分内容

        # ── 等待首屏图片 ──
        try:
            await page.evaluate("""() => {
                const imgs = Array.from(document.images);
                return Promise.all(
                    imgs.filter(i => !i.complete)
                        .map(i => new Promise(r => {
                            i.onload = r; i.onerror = r;
                            setTimeout(r, 15000);
                        }))
                );
            }""")
        except Exception:
            pass

        # ── 慢速滚动触发懒加载 ──
        try:
            h = await page.evaluate("document.body.scrollHeight")
            steps = 20
            for i in range(steps + 1):
                await page.evaluate(f"window.scrollTo(0, {int(h * i / steps)})")
                await asyncio.sleep(0.35)
            await page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass

        # ── 滚动后再次等待图片 ──
        try:
            await page.evaluate("""() => {
                const imgs = Array.from(document.images);
                return Promise.all(
                    imgs.filter(i => !i.complete)
                        .map(i => new Promise(r => {
                            i.onload = r; i.onerror = r;
                            setTimeout(r, 20000);
                        }))
                );
            }""")
        except Exception:
            pass

        # ── 用户自定义等待 ──
        await asyncio.sleep(wait)

        # ── 全页截图 ──
        fh = await page.evaluate("document.body.scrollHeight")
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp_path = tmp.name
        tmp.close()

        await page.screenshot(
            path=tmp_path, full_page=True, type="png", timeout=120000
        )
        await browser.close()

        # ── 读取截图 ──
        with open(tmp_path, "rb") as f:
            png_bytes = f.read()
        Path(tmp_path).unlink(missing_ok=True)

        return png_bytes, fh


# ── 格式转换 ─────────────────────────────────────────────

def convert_format(png_bytes: bytes, fmt: str, quality: int, pdf_mode: str):
    """将 PNG bytes 转换为所需格式，返回 (bytes, content_type, filename_suffix)"""

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
        if pdf_mode == "a4":
            pw, ph = A4  # 210 x 297 mm
            sx = pw / iw
            sh = ih * sx
            c = rc.Canvas(buf, pagesize=(pw, ph))
            y = 0
            pn = 1
            while y < sh:
                if pn > 1:
                    c.showPage()
                ps = int(y / sx)
                pe = min(ih, int((y + ph) / sx))
                stripe = img.crop((0, ps, iw, pe))
                stripe_buf = BytesIO()
                stripe.save(stripe_buf, "PNG")
                stripe_buf.seek(0)
                c.drawImage(stripe_buf, 0, ph - (pe - ps) * sx,
                            width=pw, height=(pe - ps) * sx)
                y += ph
                pn += 1
            c.save()
        elif pdf_mode == "a3":
            pw, ph = A3  # 297 x 420 mm
            sx = pw / iw
            sh = ih * sx
            c = rc.Canvas(buf, pagesize=(pw, ph))
            y = 0
            pn = 1
            while y < sh:
                if pn > 1:
                    c.showPage()
                ps = int(y / sx)
                pe = min(ih, int((y + ph) / sx))
                stripe = img.crop((0, ps, iw, pe))
                stripe_buf = BytesIO()
                stripe.save(stripe_buf, "PNG")
                stripe_buf.seek(0)
                c.drawImage(stripe_buf, 0, ph - (pe - ps) * sx,
                            width=pw, height=(pe - ps) * sx)
                y += ph
                pn += 1
            c.save()
        else:  # full
            pw, ph = iw * 0.75, ih * 0.75
            c = rc.Canvas(buf, pagesize=(pw, ph))
            c.drawImage(BytesIO(png_bytes), 0, 0, width=pw, height=ph)
            c.save()
        return buf.getvalue(), "application/pdf", ".pdf"

    return png_bytes, "image/png", ".png"


# ══════════════════════════════════════════════════════════
# API 路由
# ══════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "engine": "playwright",
        "time": datetime.now(datetime.UTC).isoformat(),
    }


@app.post("/api/capture")
async def capture(req: CaptureRequest):
    """
    使用真实 Chromium 浏览器渲染并截图

    - url: 目标网址
    - format: png / jpg / pdf
    - viewport_width: 视口宽度
    - scale: 分辨率倍数 (1/2/3)
    - wait: 额外等待秒数
    - quality: JPG 质量 (10-100)
    - pdf_mode: a4 / a3 / full
    """
    url = normalize_url(req.url)
    print(f"[Capture] {url}  fmt={req.format}  vw={req.viewport_width}  scale={req.scale}")

    try:
        png_bytes, fh = await capture_async(
            url, req.viewport_width, req.scale, req.wait
        )
    except Exception as e:
        print(f"[Capture] FAILED: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"截图失败 / Capture failed: {str(e)}",
        )

    try:
        output_bytes, content_type, suffix = convert_format(
            png_bytes, req.format, req.quality, req.pdf_mode
        )
    except Exception as e:
        print(f"[Convert] FAILED: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"格式转换失败 / Format conversion failed: {str(e)}",
        )

    slug = sanitize(url)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{slug}_{ts}{suffix}"

    print(f"[Capture] OK  {len(output_bytes)/1024:.0f}KB  →  {filename}")

    return Response(
        content=output_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Allow-Origin": "*",
        },
    )


# ── 兼容 GET 请求（方便测试） ────────────────────────────

@app.get("/api/capture")
async def capture_get(
    url: str,
    format: str = "png",
    viewport_width: int = 1280,
    scale: int = 2,
    wait: int = 3,
    quality: int = 90,
    pdf_mode: str = "a4",
):
    """GET 版本的截图接口（方便浏览器直接测试）"""
    r = CaptureRequest(
        url=url, format=format, viewport_width=viewport_width,
        scale=scale, wait=wait, quality=quality, pdf_mode=pdf_mode,
    )
    return await capture(r)


# ══════════════════════════════════════════════════════════
# 入口
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("")
    print("╔══════════════════════════════════════════╗")
    print("║    WebSnap Pro — Playwright Engine      ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║  🚀  http://0.0.0.0:{port}                  ║")
    print("║  📸  POST /api/capture                  ║")
    print("║  🏥  GET  /api/health                   ║")
    print("╚══════════════════════════════════════════╝")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=port)
