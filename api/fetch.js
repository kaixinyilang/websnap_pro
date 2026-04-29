/**
 * WebSnap Pro — Vercel Serverless 代理函数
 * Vercel serverless proxy function
 *
 * 部署后自动运行，无需管理服务器
 * Runs automatically on Vercel — no server management needed
 */

export default async function handler(req, res) {
  // ── CORS ─────────────────────────────────────────────
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', '*');
  if (req.method === 'OPTIONS') return res.status(200).end();

  // ── Health check ─────────────────────────────────────
  if (req.query.url === '__health__') {
    return res.json({ status: 'ok', time: new Date().toISOString() });
  }

  const url = req.query.url;
  if (!url) {
    return res.status(400).json({ error: 'Missing url parameter' });
  }

  console.log(`[Vercel Proxy] Fetching: ${url}`);

  try {
    const response = await fetch(url, {
      signal: AbortSignal.timeout(25000),
      headers: {
        // ── 浏览器 User-Agent ──
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
          'AppleWebKit/537.36 (KHTML, like Gecko) ' +
          'Chrome/124.0.0.0 Safari/537.36',
        Accept:
          'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        // ── 客户端特征（反反爬） ──
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1',
      },
      redirect: 'follow',
    });

    if (!response.ok) {
      return res.status(502).json({
        error: `Target server returned ${response.status} ${response.statusText}`,
      });
    }

    const html = await response.text();

    res.json({
      url: url,
      html: html,
      size: html.length,
      elapsed: 0,
    });
  } catch (err) {
    if (err.name === 'TimeoutError' || err.name === 'AbortError') {
      return res.status(504).json({ error: 'Request timeout (25s)' });
    }
    res.status(502).json({ error: `Failed to fetch page: ${err.message}` });
  }
}
