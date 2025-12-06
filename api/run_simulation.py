import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Keep compatibility with older frontend path (/api/run_simulation).
os.environ["HEADLESS"] = os.environ.get("HEADLESS") or "1"

from dwight_ultra_v2 import run_headless_simulation  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            params = parse_qs(urlparse(self.path).query)
            steps = int(params.get("steps", ["240"])[0])
            steps = max(60, min(steps, 600))

            dt_param = params.get("dt", [None])[0]
            dt = float(dt_param) if dt_param else 1 / 30.0
            dt = max(0.01, min(dt, 0.25))

            result = run_headless_simulation(steps=steps, dt=dt)
            self._respond(200, {"ok": True, "data": result})
        except Exception as exc:  # pragma: no cover - defensive
            self._respond(500, {"ok": False, "error": str(exc)})

    def _respond(self, status, payload):
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
