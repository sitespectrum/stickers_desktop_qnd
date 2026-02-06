import http.server
import socket
from urllib.parse import urlparse, parse_qs

from PySide6.QtCore import QThread, Signal


class OAuthHandler(http.server.BaseHTTPRequestHandler):
    code = None
    server_ref = None

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Login complete. You may close this window.</h1>")

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_body = self.rfile.read(content_length).decode("utf-8")
        query = parse_qs(urlparse(post_body).query)
        self.code = query["code"][0]



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
        redirect_uri = f"http://127.0.0.1:{port}/callback"

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
