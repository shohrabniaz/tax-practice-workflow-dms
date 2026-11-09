from __future__ import annotations
"""Minimal local web UI for the product automation pack."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
from src.engine import Store, seed  # noqa: E402

STORE = Store(ROOT / "output" / "records.json")
seed(STORE, ROOT / "data" / "seed_records.json")

HTML = """<!doctype html>
<html><head><meta charset='utf-8'><title>Project Console</title>
<style>
body{font-family:Segoe UI,Arial,sans-serif;margin:2rem;background:#0b1220;color:#e8eefc}
card{display:block;background:#121a2b;padding:1rem 1.25rem;border-radius:12px;margin-bottom:1rem}
a,button{color:#9ec1ff} input,select{padding:.4rem .6rem;border-radius:8px;border:1px solid #334} 
table{width:100%;border-collapse:collapse} td,th{padding:.5rem;border-bottom:1px solid #243}
.badge{padding:.15rem .5rem;border-radius:999px;background:#243556}
</style></head><body>
<h1>__TITLE__</h1>
<p>Local automation console — records backed by <code>src/engine.py</code>.</p>
<card>
<form method="POST" action="/add">
  <input name="title" placeholder="New record title" size="40" required>
  <select name="status"><option>open</option><option>in_progress</option><option>blocked</option><option>done</option></select>
  <button type="submit">Add</button>
</form>
</card>
<card>
<h3>Summary</h3>
<pre>__SUMMARY__</pre>
</card>
<card>
<h3>Records</h3>
<table><tr><th>ID</th><th>Title</th><th>Status</th><th>Action</th></tr>
__ROWS__
</table>
</card>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _page(self):
        summary = STORE.summary()
        rows = []
        for r in summary.get("records", []):
            rows.append(
                f"<tr><td>{r['id']}</td><td>{r['title']}</td>"
                f"<td><span class='badge'>{r['status']}</span></td>"
                f"<td><a href='/done?id={r['id']}'>mark done</a></td></tr>"
            )
        html = (
            HTML.replace("__TITLE__", Path(ROOT).name.replace('_', ' '))
            .replace("__SUMMARY__", json.dumps(summary.get("by_status", {}), indent=2))
            .replace("__ROWS__", "\n".join(rows) or "<tr><td colspan=4>No records</td></tr>")
        )
        data = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/done":
            q = parse_qs(u.query)
            rid = (q.get("id") or [""])[0]
            if rid:
                STORE.set_status(rid, "done")
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return
        if u.path in ("/", "/index"):
            self._page()
            return
        self.send_error(404)

    def do_POST(self):
        u = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        form = parse_qs(body)
        if u.path == "/add":
            title = (form.get("title") or [""])[0].strip()
            status = (form.get("status") or ["open"])[0]
            if title:
                STORE.add(title, status)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()


def main(host: str = "127.0.0.1", port: int = 8765):
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"Open http://{host}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
