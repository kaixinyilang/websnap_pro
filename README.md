# WebSnap Pro

> 通用网页全页截图工具 · 输入网址，一键截取完整网页，支持 PNG / JPG / PDF 导出  
> Universal web page screenshot tool — enter a URL, capture the full page, export as PNG / JPG / PDF

![screenshot](https://img.shields.io/badge/stack-html2canvas_+_Express-blueviolet)
![deploy](https://img.shields.io/badge/deploy-Vercel-black)

---

## 🇨🇳 中文说明

### 简介

WebSnap Pro 是一个纯前端 + 后端代理的网页截图工具。它通过后端服务器获取目标网页的 HTML，在前端用 html2canvas 渲染并截图，支持多种输出格式。

### 功能特性

- 🔗 输入任意网址，自动获取页面内容
- 🖼️ 全页截图，支持**懒加载滚动触发**
- 🎨 三种输出格式：**PNG**（无损）、**JPG**（可调质量）、**PDF**（A4/A3/长图）
- 📐 可调截图宽度（320-3840px）和分辨率倍数（1×/2×）
- ⏱️ 可配置额外等待时间，确保动态内容加载完成
- 📋 实时进度条 + 彩色日志输出
- 🚀 一键部署到 Vercel（免费）

### 目录结构

```
websnap-pro/
├── websnap_pro.html      # 前端主页面（含完整 UI 和截图逻辑）
├── api/
│   └── fetch.js          # Vercel Serverless 代理函数
├── vercel.json           # Vercel 部署配置文件
├── package.json          # 本地开发依赖（Node.js）
├── server.js             # 本地 Node.js 后端服务器
├── server.py             # 本地 Python 后端服务器
└── README.md             # 本文件
```

### 部署方式

#### 方式一：部署到 Vercel（推荐）

1. 将本项目推送到 GitHub 仓库
2. 在 [vercel.com](https://vercel.com) 点击 **"Add New Project"**
3. 导入该仓库，Vercel 自动识别 `vercel.json` 配置
4. 部署完成，获得可公开访问的 URL

> Vercel 会自动运行 `api/fetch.js` 作为无服务器代理函数，无需配置任何服务器。

#### 方式二：本地运行（需 Node.js 18+）

```bash
# 安装依赖
npm install

# 启动服务器
node server.js

# 浏览器打开
open http://localhost:3000
```

#### 方式三：Python 本地运行

```bash
pip install flask requests
python server.py
# 访问 http://localhost:3000
```

### 使用方法

1. 输入目标网址（如 `https://www.baidu.com`）
2. 选择输出格式（PNG / JPG / PDF）
3. 调整截图参数（宽度、等待时间、分辨率）
4. 点击 **"开始截图"**
5. 预览结果并下载

---

## 🇬🇧 English

### Overview

WebSnap Pro is a web page screenshot tool with a frontend UI and backend proxy. The backend fetches target page HTML, then html2canvas renders and captures it in the browser. Multiple export formats are supported.

### Features

- 🔗 Enter any URL — the backend proxy fetches the page content
- 🖼️ Full-page capture with **lazy-load scroll trigger**
- 🎨 Three output formats: **PNG** (lossless), **JPG** (adjustable quality), **PDF** (A4/A3/full)
- 📐 Configurable capture width (320–3840px) and scale (1×/2×)
- ⏱️ Adjustable extra wait time for dynamic content
- 📋 Real-time progress bar + color-coded logs
- 🚀 One-click deploy to Vercel (free tier)

### Directory Structure

```
websnap-pro/
├── websnap_pro.html      # Frontend page (UI + capture logic)
├── api/
│   └── fetch.js          # Vercel serverless proxy function
├── vercel.json           # Vercel deployment config
├── package.json          # Local dev dependencies (Node.js)
├── server.js             # Local Node.js backend server
├── server.py             # Local Python backend server
└── README.md             # This file
```

### Deployment

#### Option 1: Deploy to Vercel (Recommended)

1. Push this repo to GitHub
2. Go to [vercel.com](https://vercel.com) and click **"Add New Project"**
3. Import your GitHub repository — Vercel auto-detects `vercel.json`
4. Deploy and get a public URL

> Vercel runs `api/fetch.js` as a serverless function automatically. No server management needed.

#### Option 2: Run Locally (Node.js 18+)

```bash
npm install
node server.js
# Open http://localhost:3000
```

#### Option 3: Run Locally (Python)

```bash
pip install flask requests
python server.py
# Open http://localhost:3000
```

### Usage

1. Enter a target URL (e.g. `https://example.com`)
2. Choose output format (PNG / JPG / PDF)
3. Adjust capture parameters (width, wait time, scale)
4. Click **"Start Capture"**
5. Preview the result and download

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla JS + [Tailwind CSS](https://tailwindcss.com/) + [html2canvas](https://html2canvas.hertzen.com/) + [jsPDF](https://github.com/parallax/jsPDF) |
| Backend Proxy | [Express](https://expressjs.com/) (Node.js) or [Flask](https://flask.palletsprojects.com/) (Python) |
| Serverless | [Vercel](https://vercel.com/) with `@vercel/node` runtime |
| Design | Dark theme with indigo-purple gradient (inspired by ai66.org) |

## License

MIT
