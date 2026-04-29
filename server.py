"""
WebSnap Pro — 后端代理服务器 / Backend Proxy Server (Python)

安装依赖 / Install:
  pip install flask requests

启动 / Run:
  python server.py

访问 / Open:
  http://localhost:3000

部署到 Vercel 时无需此文件。
This file is for local dev only. Vercel uses api/fetch.js instead.
"""

import sys
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_from_directory
    import requests
except ImportError:
    print("\n Missing dependencies / 缺少依赖")
    print("  pip install flask requests\n")
    sys.exit(1)

app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def index():
    return send_from_directory('.', 'websnap_pro.html')

@app.route('/<path:path>')
def static_files(path):
    p = Path(path)
    if p.exists() and not path.startswith('api/'):
        return send_from_directory('.', path)
    return send_from_directory('.', 'websnap_pro.html')


@app.route('/api/fetch')
def proxy_fetch():
    url = request.args.get('url')
    if not url:
        return {'error': 'Missing url parameter / 缺少 url 参数'}, 400

    print(f'[Proxy] Fetching: {url}')

    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept': (
            'text/html,application/xhtml+xml,application/xml;q=0.9,'
            'image/avif,image/webp,image/apng,*/*;q=0.8'
        ),
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
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
    }

    try:
        resp = requests.get(url, headers=headers, timeout=25, allow_redirects=True)
        resp.encoding = 'utf-8'

        if resp.status_code != 200:
            return {'error': f'Target returned / 目标返回 {resp.status_code}'}, 502

        html = resp.text
        size_kb = len(html) / 1024
        print(f'[Proxy] OK {url}  {size_kb:.1f}KB')

        return {
            'url': url,
            'html': html,
            'size': len(html),
            'elapsed': int(resp.elapsed.total_seconds() * 1000),
        }

    except requests.Timeout:
        print(f'[Proxy] Timeout: {url}')
        return {'error': 'Request timeout / 请求超时 (25s)'}, 504
    except Exception as e:
        print(f'[Proxy] Failed: {url}  -  {e}')
        return {'error': f'Failed to fetch / 获取失败: {e}'}, 502


@app.route('/api/health')
def health():
    from datetime import datetime
    return {'status': 'ok', 'time': datetime.now().isoformat()}


if __name__ == '__main__':
    PORT = 3000
    print('')
    print('╔══════════════════════════════════════════╗')
    print('║           WebSnap Pro Server            ║')
    print('╠══════════════════════════════════════════╣')
    print(f'║  🌐  http://localhost:{PORT}                ║')
    print(f'║  🚀  Proxy ready / 代理已就绪           ║')
    print('╚══════════════════════════════════════════╝')
    print('')
    app.run(host='0.0.0.0', port=PORT, debug=False)
