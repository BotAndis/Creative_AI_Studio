"""
Tiny local CORS proxy for SAIA / Academic Cloud API.
Run once: python saia_proxy.py
Then open plotter_studio.html in your browser.
The proxy listens on http://localhost:8765 and forwards to chat-ai.academiccloud.de.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.request, urllib.error, json, sys, time

TARGET  = "https://chat-ai.academiccloud.de"
PORT    = 8765
TIMEOUT = 300          # seconds to wait on the upstream API
RETRIES = 3            # extra attempts when the model is still warming up
BACKOFF = 4            # seconds between retries

CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS,DELETE,PUT",
    "Access-Control-Allow-Headers": "Authorization,Content-Type,Accept",
}

# Upstream statuses that mean "transient — retry" (model cold-start / overloaded).
RETRYABLE = {500, 502, 503, 504}


class Proxy(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        # ASCII only + never raise: a logging error must not abort the response
        # (Windows consoles default to cp1252 and choke on non-ASCII).
        try:
            print(f"  {self.address_string()} -> {fmt % args}")
        except Exception:
            pass

    def _cors(self):
        for k, v in CORS.items():
            self.send_header(k, v)

    def _safe_write(self, status, ctype, data):
        """Send a response, swallowing aborts when the client already hung up."""
        try:
            self.send_response(status)
            self._cors()
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            # Client navigated away / cancelled the request — not our problem.
            print("  (client closed connection before response was sent)")

    def do_OPTIONS(self):
        try:
            self.send_response(200)
            self._cors()
            self.send_header("Content-Length", "0")
            self.end_headers()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def _forward(self, method):
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length) if length else None
        url    = TARGET + self.path

        fwd_headers = {}
        for h in ("Authorization", "Content-Type", "Accept"):
            if self.headers.get(h):
                fwd_headers[h] = self.headers[h]

        last_status, last_data = 502, b'{"error":"proxy: no upstream response"}'

        for attempt in range(RETRIES + 1):
            req = urllib.request.Request(url, data=body, headers=fwd_headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    data  = resp.read()
                    ctype = resp.headers.get("Content-Type", "application/json")
                    self._safe_write(resp.status, ctype, data)
                    return
            except urllib.error.HTTPError as e:
                last_data   = e.read() or f'{{"error":"upstream HTTP {e.code}"}}'.encode()
                last_status = e.code
                ctype       = e.headers.get("Content-Type", "application/json") if e.headers else "application/json"
                if e.code in RETRYABLE and attempt < RETRIES:
                    print(f"  upstream {e.code} — retry {attempt + 1}/{RETRIES} in {BACKOFF}s")
                    time.sleep(BACKOFF)
                    continue
                self._safe_write(last_status, ctype, last_data)
                return
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                # DNS / connection / timeout failure reaching the API.
                last_status = 502
                last_data   = json.dumps({"error": f"proxy: cannot reach upstream ({e})"}).encode()
                if attempt < RETRIES:
                    print(f"  upstream unreachable ({e}) — retry {attempt + 1}/{RETRIES} in {BACKOFF}s")
                    time.sleep(BACKOFF)
                    continue
                self._safe_write(last_status, "application/json", last_data)
                return

    def do_POST(self):
        self._forward("POST")

    def do_GET(self):
        self._forward("GET")

    def do_PUT(self):
        self._forward("PUT")

    def do_DELETE(self):
        self._forward("DELETE")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("localhost", PORT), Proxy)
    print(f"SAIA proxy running on http://localhost:{PORT}")
    print(f"Forwarding to {TARGET}")
    print("Set proxy URL in Plotter Studio to:  http://localhost:8765/")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")
        sys.exit(0)
