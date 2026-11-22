# PrintScale AuraSR server: lets the PrintScale Android app use this notebook's GPU.
# The app uploads its prepared artwork, this server runs AuraSR 4x, the app downloads the result
# and does everything else (print sizing, DPI, colour profile, file export) on the phone.
#
# API (every request needs the header X-PrintScale-Key):
#   GET    /health            -> {"printscale": 1, "model", "device", "gpu", "max_pixels"}
#   POST   /jobs              body = PNG or JPEG  -> {"id"}
#   GET    /jobs/<id>         -> {"state": queued|running|done|failed|cancelled, "done", "total", "error"}
#   GET    /jobs/<id>/result  -> 4x PNG (RGBA if the upload had transparency)
#   DELETE /jobs/<id>         -> cancels and deletes the job
# Jobs are asynchronous because tunnels close requests that wait more than about 100 s.

import html
import io
import json
import os
import queue
import re
import secrets
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote

from PIL import Image

import printscale_aurasr as ps

MAX_UPLOAD_BYTES = 200 * 2**20
MAX_PIXELS = 4096 * 4096      # same limit as the app's planner
JOB_TTL_SECONDS = 3600


class Job:
    def __init__(self, path):
        self.id = uuid.uuid4().hex
        self.state = "queued"
        self.done = 0
        self.total = 0
        self.error = None
        self.input = path
        self.output = None
        self.created = time.time()
        self.cancel = threading.Event()

    def json(self):
        return {"id": self.id, "state": self.state, "done": self.done, "total": self.total, "error": self.error}


class PrintScaleServer:
    def __init__(self, model, device, port=8765, key=None, log=print):
        self.model, self.device, self.port, self.log = model, device, port, log
        self.key = key or secrets.token_urlsafe(18)
        self.workdir = tempfile.mkdtemp(prefix="printscale_")
        self.jobs = {}
        self.queue = queue.Queue()
        self.lock = threading.Lock()
        self.httpd = None
        self.tunnel = None
        self.public_url = None
        import torch
        self.gpu = torch.cuda.get_device_name(0) if device == "cuda" else ""

    # ------------------------------------------------------------------ GPU worker (one job at a time)
    def _worker(self):
        import torch
        while True:
            job = self.queue.get()
            if job.cancel.is_set():
                continue
            job.state = "running"
            t0 = time.time()
            try:
                img = Image.open(job.input)
                img.load()
                alpha = img.getchannel("A") if img.mode in ("RGBA", "LA") else None
                rgb = img.convert("RGB")

                def progress(d, t):
                    job.done, job.total = d, t

                batch, block = ps.default_batch(), 512  # 512 px blocks keep memory low and progress smooth
                for attempt in range(4):
                    try:
                        out = ps.ai_upscale_4x(self.model, rgb, block=block, batch=batch, progress=progress,
                                               cancelled=job.cancel.is_set)
                        break
                    except torch.cuda.OutOfMemoryError:
                        torch.cuda.empty_cache()
                        batch = max(1, batch // 2)
                        self.log(f"GPU memory full, retrying with batch {batch}")
                else:
                    raise RuntimeError("Not enough GPU memory for this image.")
                if alpha is not None:
                    out.putalpha(alpha.resize(out.size, Image.BICUBIC))
                job.output = os.path.join(self.workdir, job.id + "_out.png")
                out.save(job.output, "PNG", compress_level=4)
                job.state = "done"
                self.log(f"job {job.id[:8]}: {rgb.width}x{rgb.height} -> {out.width}x{out.height} in {time.time() - t0:.0f}s")
            except InterruptedError:
                job.state = "cancelled"
            except Exception as e:
                job.state, job.error = "failed", f"{type(e).__name__}: {e}"
                self.log(f"job {job.id[:8]} failed: {job.error}")
            finally:
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                if os.path.exists(job.input):
                    os.remove(job.input)

    def _janitor(self):
        while True:
            time.sleep(300)
            now = time.time()
            with self.lock:
                old = [j for j in self.jobs.values() if now - j.created > JOB_TTL_SECONDS]
                for j in old:
                    self._delete(j)

    def _delete(self, job):
        job.cancel.set()
        for p in (job.input, job.output):
            if p and os.path.exists(p):
                os.remove(p)
        self.jobs.pop(job.id, None)

    # ------------------------------------------------------------------ HTTP
    def _handler(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def _send_json(self, code, obj):
                body = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _authorized(self):
                got = self.headers.get("X-PrintScale-Key") or ""
                if not got:
                    m = re.search(r"[?&]key=([^&]+)", self.path)
                    got = m.group(1) if m else ""
                return secrets.compare_digest(got, server.key)

            def _job(self, jid):
                job = server.jobs.get(jid)
                if job is None:
                    self._send_json(404, {"error": "No such job. The notebook may have restarted."})
                return job

            def do_GET(self):
                path = self.path.split("?")[0]
                if path in ("/", "/connect"):
                    return self._connect_page()
                if not self._authorized():
                    return self._send_json(401, {"error": "Wrong key."})
                if path == "/health":
                    return self._send_json(200, {"printscale": 1, "model": "AuraSR v2", "device": server.device,
                                                 "gpu": server.gpu, "max_pixels": MAX_PIXELS})
                m = re.fullmatch(r"/jobs/([0-9a-f]{32})(/result)?", path)
                if not m:
                    return self._send_json(404, {"error": "Unknown path."})
                job = self._job(m.group(1))
                if job is None:
                    return
                if not m.group(2):
                    return self._send_json(200, job.json())
                if job.state != "done":
                    return self._send_json(409, {"error": f"Job is {job.state}."})
                size = os.path.getsize(job.output)
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(size))
                self.end_headers()
                with open(job.output, "rb") as f:
                    shutil.copyfileobj(f, self.wfile, 1 << 20)

            def do_POST(self):
                if not self._authorized():
                    return self._send_json(401, {"error": "Wrong key."})
                if self.path.split("?")[0] != "/jobs":
                    return self._send_json(404, {"error": "Unknown path."})
                length = int(self.headers.get("Content-Length") or 0)
                if length <= 0:
                    return self._send_json(411, {"error": "Empty upload."})
                if length > MAX_UPLOAD_BYTES:
                    return self._send_json(413, {"error": "Upload is larger than 200 MB."})
                path = os.path.join(server.workdir, uuid.uuid4().hex + "_in")
                left = length
                with open(path, "wb") as f:
                    while left > 0:
                        chunk = self.rfile.read(min(1 << 20, left))
                        if not chunk:
                            break
                        f.write(chunk)
                        left -= len(chunk)
                if left:
                    os.remove(path)
                    return self._send_json(400, {"error": "Upload was cut off."})
                try:
                    with Image.open(path) as im:
                        w, h = im.size
                        im.verify()
                except Exception:
                    os.remove(path)
                    return self._send_json(400, {"error": "The upload is not an image."})
                if w * h > MAX_PIXELS:
                    os.remove(path)
                    return self._send_json(413, {"error": f"{w}x{h} is over the server's {MAX_PIXELS // 10**6} MP limit."})
                job = Job(path)
                with server.lock:
                    server.jobs[job.id] = job
                server.queue.put(job)
                server.log(f"job {job.id[:8]}: received {w}x{h}")
                self._send_json(200, {"id": job.id})

            def do_DELETE(self):
                if not self._authorized():
                    return self._send_json(401, {"error": "Wrong key."})
                m = re.fullmatch(r"/jobs/([0-9a-f]{32})", self.path.split("?")[0])
                job = server.jobs.get(m.group(1)) if m else None
                if job:
                    with server.lock:
                        server._delete(job)
                self._send_json(200, {"ok": True})

            def _connect_page(self):
                # Opened by scanning the QR code on a phone: one tap hands the link to the app.
                if not self._authorized():
                    body = b"<h1>PrintScale server</h1><p>Open the full link from the notebook.</p>"
                    self.send_response(401)
                else:
                    base = server.public_url or f"http://localhost:{server.port}"
                    deep = f"printscale://connect?server={quote(base, safe='')}&key={quote(server.key, safe='')}"
                    full = f"{base}/?key={server.key}"
                    body = f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PrintScale server</title></head><body style="font-family:sans-serif;background:#121110;color:#f2eee6;padding:24px">
<h1 style="font-weight:500">PrintScale cloud GPU</h1>
<p>AuraSR v2 is running on {html.escape(server.gpu or server.device)}.</p>
<p><a href="{html.escape(deep)}" style="display:inline-block;background:#ea6440;color:#1a0f0b;padding:14px 20px;border-radius:10px;text-decoration:none;font-weight:600">Open in the PrintScale app</a></p>
<p>Or copy this link and paste it in the app:</p><p style="word-break:break-all;color:#b8b1a6">{html.escape(full)}</p>
</body></html>""".encode()
                    self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        return Handler

    def start(self):
        threading.Thread(target=self._worker, daemon=True).start()
        threading.Thread(target=self._janitor, daemon=True).start()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", self.port), self._handler())
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def start_tunnel(self, binary="./cloudflared", timeout=60):
        """Opens a free Cloudflare quick tunnel (no account) and returns the public https URL."""
        if not os.path.exists(binary):
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
            subprocess.run(["wget", "-q", "-O", binary, url], check=True)
            os.chmod(binary, 0o755)
        self.tunnel = subprocess.Popen([binary, "tunnel", "--url", f"http://127.0.0.1:{self.port}", "--no-autoupdate"],
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        deadline = time.time() + timeout
        for line in self.tunnel.stdout:
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
            if m:
                self.public_url = m.group(0)
                threading.Thread(target=lambda: [None for _ in self.tunnel.stdout], daemon=True).start()  # keep draining
                return self.public_url
            if time.time() > deadline:
                break
        raise RuntimeError("The Cloudflare tunnel did not start. Run this cell again.")

    @property
    def link(self):
        return f"{self.public_url or f'http://localhost:{self.port}'}/?key={self.key}"

    def status_line(self):
        states = [j.state for j in list(self.jobs.values())]
        running = [j for j in self.jobs.values() if j.state == "running"]
        now = f" | running: {100 * running[0].done // max(1, running[0].total)}%" if running else ""
        return f"{time.strftime('%H:%M:%S')} jobs: {len(states)} ({states.count('done')} done){now}"
