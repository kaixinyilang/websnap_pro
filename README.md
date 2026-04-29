# WebSnap Pro

> 通用网页全页截图工具 · 输入网址，一键截取完整网页，支持 PNG / JPG / PDF 导出  
> Universal web page screenshot tool — enter a URL, capture the full page, export as PNG / JPG / PDF

![screenshot](https://img.shields.io/badge/stack-Playwright_+_html2canvas-blueviolet)
![deploy](https://img.shields.io/badge/deploy-Vercel_+_Render-black)

---

## 🇨🇳 中文说明

### 简介

WebSnap Pro 是一个网页截图工具，提供**两种截图引擎**：

| 引擎 | 说明 | 适用场景 |
|------|------|----------|
| ☁ **Vercel 云端** | Vercel 服务器代理 + html2canvas 前端渲染 | 普通网站，零配置 |
| 🎯 **Playwright 专业引擎** | 真实 Chromium 浏览器渲染 | 有反爬保护的网站（如 Alibaba、电商网站等） |

### 功能特性

- 🔗 输入任意网址，自动获取页面内容
- 🖼️ 全页截图，支持**懒加载滚动触发**
- 🎨 三种输出格式：**PNG**（无损）、**JPG**（可调质量）、**PDF**（A4/A3/长图）
- 📐 可调截图宽度（320-3840px）和分辨率倍数（1×/2×）
- ⏱️ 可配置额外等待时间，确保动态内容加载完成
- 📋 实时进度条 + 彩色日志输出
- 🚀 Vercel 部署（云端代理，零配置） + Render 部署（Playwright 专业引擎）

### 目录结构

```
websnap-pro/
├── websnap_pro.html                # 前端主页面（含完整 UI 和截图逻辑）
├── api/
│   └── fetch.js                    # Vercel Serverless 代理函数
├── vercel.json                     # Vercel 部署配置文件
├── package.json                    # 本地开发依赖（Node.js）
├── server.js                       # 本地 Node.js 后端服务器
├── server.py                       # 本地 Python 后端服务器
├── render-playwright-server.py     # Playwright 专业截图引擎（部署到 Render）
├── requirements-playwright.txt     # Playwright 引擎依赖
└── README.md                       # 本文件
```

### 部署方式

#### 方案一：Vercel 部署（前端 + 云端代理）

适合大多数普通网站，零配置，分享给他人直接使用。

1. 将本项目推送到 GitHub 仓库
2. 在 [vercel.com](https://vercel.com) 点击 **"Add New Project"**
3. 导入该仓库，Vercel 自动识别 `vercel.json` 配置
4. 部署完成，获得可公开访问的 URL

> Vercel 会自动运行 `api/fetch.js` 作为无服务器代理函数，无需配置任何服务器。
> 前端的引擎切换为"Vercel 云端"模式即可使用。

#### 方案二：Vercel + Render 部署（完整方案）

适合需要截取有反爬保护的网站（Alibaba、电商等），需要额外部署 Playwright 引擎。

**步骤 1：部署到 Vercel（同上）**

**步骤 2：部署 Playwright 引擎到 Render**

1. 将本仓库推送到 GitHub
2. 在 [render.com](https://render.com) 点击 **"New Web Service"**
3. 导入该仓库
4. 配置以下参数：
   - **Name**: `websnap-pro-playwright`（任意）
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements-playwright.txt && python -m playwright install chromium
     ```
   - **Start Command**:
     ```bash
     python render-playwright-server.py
     ```
   - **Plan**: 选择 Free（免费版够用，750小时/月）
5. 点击 **"Create Web Service"**，等待构建和部署完成
6. 部署完成后获得 URL：`https://your-app.onrender.com`

**步骤 3：前端配置**

1. 打开 Vercel 部署的 WebSnap Pro 页面
2. 在"截图引擎"部分切换为 **Playwright** 模式
3. 填入 Render 后端地址：`https://your-app.onrender.com`
4. 输入目标网址，点击"开始截图"

> **提示**：Render 免费版在 15 分钟无活动后会休眠，下次请求首次会有约 30 秒冷启动延迟，后续请求正常。

#### 方案三：本地运行（需 Node.js 18+）

```bash
# 安装依赖
npm install

# 启动服务器
node server.js

# 浏览器打开
open http://localhost:3000
```

#### 方案四：Python 本地运行

```bash
pip install flask requests
python server.py
# 访问 http://localhost:3000
```

#### 方案五：本地运行 Playwright 引擎（调试用）

```bash
pip install -r requirements-playwright.txt
python -m playwright install chromium
python render-playwright-server.py
# Playwright 引擎启动在 http://localhost:8000
# 前端切换到 Playwright 模式，地址填写 http://localhost:8000
```

### 使用方法

1. 输入目标网址（如 `https://www.baidu.com`）
2. 选择截图引擎：
   - **Vercel 云端**：普通网站，直接使用
   - **Playwright**：反爬严格的网站，需配置后端地址
3. 选择输出格式（PNG / JPG / PDF）
4. 调整截图参数（宽度、等待时间、分辨率）
5. 点击 **"开始截图"**
6. 预览结果并下载

### 常见问题

**Q: 截图结果只显示验证码/滑块界面？**
A: 该网站有反爬保护。请切换到 **Playwright 引擎** 模式，部署 Playwright 后端后即可正常截图。

**Q: Playwright 引擎需要额外付费吗？**
A: Render 免费版（750 小时/月）足够个人使用。如果流量较大，可升级到付费版（$7/月起）。

**Q: Render 为什么第一次请求很慢？**
A: 免费版在 15 分钟无活动后会休眠，下次请求需要启动（约 30 秒）。之后请求正常速度。

---

## 🇬🇧 English

### Overview

WebSnap Pro is a web page screenshot tool with **two capture engines**:

| Engine | Description | Use Case |
|--------|-------------|----------|
| ☁ **Vercel Cloud** | Vercel serverless proxy + html2canvas frontend rendering | Normal websites, zero setup |
| 🎯 **Playwright Pro** | Real Chromium browser rendering | Protected websites (Alibaba, e-commerce, etc.) |

### Features

- 🔗 Enter any URL — the backend proxy fetches the page content
- 🖼️ Full-page capture with **lazy-load scroll trigger**
- 🎨 Three output formats: **PNG** (lossless), **JPG** (adjustable quality), **PDF** (A4/A3/full)
- 📐 Configurable capture width (320–3840px) and scale (1×/2×)
- ⏱️ Adjustable extra wait time for dynamic content
- 📋 Real-time progress bar + color-coded logs
- 🚀 Deploy to Vercel (cloud proxy) + Render (Playwright engine)

### Directory Structure

```
websnap-pro/
├── websnap_pro.html             # Frontend page (UI + capture logic)
├── api/
│   └── fetch.js                 # Vercel serverless proxy function
├── vercel.json                  # Vercel deployment config
├── package.json                 # Local dev dependencies (Node.js)
├── server.js                    # Local Node.js backend server
├── server.py                    # Local Python backend server
├── render-playwright-server.py  # Playwright engine (deploy to Render)
├── requirements-playwright.txt  # Playwright engine dependencies
└── README.md                    # This file
```

### Deployment

#### Option 1: Vercel Only (Cloud Proxy)

For most websites — zero setup, shareable with anyone.

1. Push this repo to GitHub
2. Go to [vercel.com](https://vercel.com) and click **"Add New Project"**
3. Import your GitHub repository — Vercel auto-detects `vercel.json`
4. Deploy and get a public URL
5. Switch to "Vercel 云端" mode in the frontend

#### Option 2: Vercel + Render (Full Solution)

For websites with anti-bot protection.

**Step 1: Deploy to Vercel** (same as above)

**Step 2: Deploy Playwright Engine to Render**

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) and click **"New Web Service"**
3. Import the repository
4. Set the following:
   - **Build Command**:
     ```bash
     pip install -r requirements-playwright.txt && python -m playwright install chromium
     ```
   - **Start Command**:
     ```bash
     python render-playwright-server.py
     ```
   - **Plan**: Free (750 hours/month)
5. Click **"Create Web Service"**
6. Once deployed, get your URL: `https://your-app.onrender.com`

**Step 3: Configure Frontend**

1. Open WebSnap Pro on your Vercel URL
2. Switch to **Playwright** engine mode
3. Enter the Render URL: `https://your-app.onrender.com`
4. Enter target URL and click "Start Capture"

> **Note**: Render's free tier spins down after 15 minutes of inactivity. The first request after idle will have ~30s cold start delay.

#### Option 3: Run Locally (Node.js 18+)

```bash
npm install
node server.js
# Open http://localhost:3000
```

#### Option 4: Run Locally (Python)

```bash
pip install flask requests
python server.py
# Open http://localhost:3000
```

#### Option 5: Run Playwright Engine Locally

```bash
pip install -r requirements-playwright.txt
python -m playwright install chromium
python render-playwright-server.py
# Playwright engine runs at http://localhost:8000
# Set frontend to Playwright mode with this URL
```

### Usage

1. Enter a target URL (e.g. `https://example.com`)
2. Choose capture engine:
   - **Vercel Cloud**: For normal sites
   - **Playwright**: For protected sites (requires backend URL)
3. Choose output format (PNG / JPG / PDF)
4. Adjust capture parameters (width, wait time, scale)
5. Click **"Start Capture"**
6. Preview the result and download

### FAQ

**Q: Screenshot only shows a captcha/verification page?**
A: That website has anti-bot protection. Switch to **Playwright engine** mode and deploy the Playwright backend to Render.

**Q: Does Playwright engine cost extra?**
A: Render's free tier (750 hours/month) is sufficient for personal use. Paid plans start at $7/month for higher traffic.

**Q: Why is the first request slow on Render?**
A: The free tier spins down after 15 minutes of inactivity. First request after idle takes ~30s to start. After that, requests are normal speed.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla JS + [Tailwind CSS](https://tailwindcss.com/) + [html2canvas](https://html2canvas.hertzen.com/) + [jsPDF](https://github.com/parallax/jsPDF) |
| Backend Proxy | [Express](https://expressjs.com/) (Node.js) or [Flask](https://flask.palletsprojects.com/) (Python) |
| Playwright Engine | [FastAPI](https://fastapi.tiangolo.com/) + [Playwright](https://playwright.dev/) + [Pillow](https://python-pillow.org/) + [ReportLab](https://www.reportlab.com/) |
| Cloud Proxy | [Vercel](https://vercel.com/) with `@vercel/node` runtime |
| Playwright Hosting | [Render](https://render.com/) (free tier) |
| Design | Dark theme with indigo-purple gradient (inspired by ai66.org) |

## License

MIT
