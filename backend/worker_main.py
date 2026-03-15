import threading
import os
import pathlib
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler


class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


# Write Firebase credentials from env var to file path if provided
firebase_creds = os.environ.get("FIREBASE_CREDENTIALS")
firebase_creds_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
if firebase_creds and firebase_creds_path:
    p = pathlib.Path(firebase_creds_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(firebase_creds)
    print(f"Firebase credentials written to {firebase_creds_path}", flush=True)

port = int(os.environ.get("PORT", 8080))
server = HTTPServer(("", port), Health)
t = threading.Thread(target=server.serve_forever, daemon=True)
t.start()
print(f"Health server listening on port {port}", flush=True)

subprocess.run(
    ["celery", "-A", "app.worker.celery_app", "worker", "--loglevel=info"]
)
