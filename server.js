/**
 * WebSnap Pro — 后端代理服务器 / Backend Proxy Server (Node.js)
 *
 * 需要 Node.js 18+（内置 fetch API）
 * 启动: node server.js
 * 访问: http://localhost:3000
 *
 * 部署到 Vercel 时无需此文件，Vercel 会自动运行 api/fetch.js
 * This file is for local dev only. Vercel uses api/fetch.js instead.
 */

const express = require('express');
const app = express();

const PORT = process.env.PORT || 3000;

// ── CORS ───────────────────────────────────────────────
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', '*');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

// ── Serve static files ─────────────────────────────────
app.use(express.static(__dirname));

// ── Proxy API ──────────────────────────────────────────
app.get('/api/fetch', async (req, res) => {
  const url = req.query.url;
  if (!url) {
    return res.status(400).json({ error: 'Missing url parameter / 缺少 url 参数' });
  }

  console.log(`[Proxy] Fetching: ${url}`);
  const startTime = Date.now();

  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 25000);

    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
          'AppleWebKit/537.36 (KHTML, like Gecko) ' +
          'Chrome/124.0.0.0 Safari/537.36',
        Accept:
          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
      },
      redirect: 'follow',
    });

    clearTimeout(timeout);

    if (!response.ok) {
      return res.status(502).json({
        error: `Target server returned / 目标服务器返回 ${response.status} ${response.statusText}`,
      });
    }

    const html = await response.text();
    const elapsed = Date.now() - startTime;
    const sizeKB = (html.length / 1024).toFixed(1);

    console.log(`[Proxy] OK ${url}  ${sizeKB}KB  ${elapsed}ms`);

    res.json({ url, html, size: html.length, elapsed });
  } catch (err) {
    if (err.name === 'AbortError') {
      console.log(`[Proxy] Timeout: ${url}`);
      return res.status(504).json({ error: 'Request timeout / 请求超时 (25s)' });
    }
    console.log(`[Proxy] Failed: ${url}  -  ${err.message}`);
    res.status(502).json({ error: `Failed to fetch page / 获取页面失败: ${err.message}` });
  }
});

// ── Health check ───────────────────────────────────────
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', time: new Date().toISOString() });
});

// ── Start ──────────────────────────────────────────────
app.listen(PORT, '0.0.0.0', () => {
  console.log('');
  console.log('╔══════════════════════════════════════════╗');
  console.log('║           WebSnap Pro Server            ║');
  console.log('╠══════════════════════════════════════════╣');
  console.log(`║  🌐  http://localhost:${PORT}                ║`);
  console.log(`║  🚀  Proxy ready / 代理已就绪           ║`);
  console.log('╚══════════════════════════════════════════╝');
  console.log('');
});
