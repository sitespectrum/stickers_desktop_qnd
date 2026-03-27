import http.server
import socket
from urllib.parse import urlparse, parse_qs

from PySide6.QtCore import QThread, Signal

from globals.constants import FRONTEND


class OAuthHandler(http.server.BaseHTTPRequestHandler):
    code = None
    server_ref = None

    ABORT_CODE = "__OAUTH_ABORT__"

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", FRONTEND)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/callback/abort":
            OAuthHandler.code = OAuthHandler.ABORT_CODE

            self.send_response(200, "Aborted.")
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b"<h1>Login aborted. You may close this window.</h1>")

            return

        params = parse_qs(parsed.query)

        code = params.get("code", [None])[0]
        if code:
            OAuthHandler.code = code

        if code:
            self.send_response(200, "Code received.")
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b"<h1>Login complete. You may close this window.</h1>")
        else:
            self.send_response(400, "Missing code parameter.")
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(b"<h1>Missing code parameter.</h1>")

    def log_message(self, format, *args):
        return


def get_free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class OAuthServerThread(QThread):
    server_started = Signal(str)

    def __init__(self):
        super().__init__()
        self.server = None
        self.http_thread = None

    def run_http_server(self):
        self.server.serve_forever()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()

        if self.http_thread and self.http_thread.is_alive():
            self.http_thread.join(timeout=1)

    def run(self):
        port = get_free_port()
        redirect_uri = f"http://localhost:{port}/callback"

        # noinspection PyTypeChecker
        self.server = http.server.HTTPServer(("127.0.0.1", port), OAuthHandler)
        OAuthHandler.server_ref = self.server

        self.server_started.emit(redirect_uri)

        import threading
        self.http_thread = threading.Thread(target=self.run_http_server, daemon=True)
        self.http_thread.start()

        self.exec()


class OAuthWaitThread(QThread):
    code_received = Signal(str)

    def run(self):
        while OAuthHandler.code is None:
            self.msleep(100)

        self.code_received.emit(OAuthHandler.code)
