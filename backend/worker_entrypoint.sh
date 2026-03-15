#!/bin/sh
# Start a minimal HTTP health server on $PORT alongside the Celery worker
python3 -c "
import threading, os
from http.server import HTTPServer, BaseHTTPRequestHandler

class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')
    def log_message(self, *args):
        pass

port = int(os.environ.get('PORT', 8080))
server = HTTPServer(('', port), Health)
t = threading.Thread(target=server.serve_forever, daemon=True)
t.start()
" &

exec celery -A app.worker.celery_app worker --loglevel=info
