import contextlib
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from harness.liveness import ModelServerDown, check_model_server_alive


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("localhost", 0))
        return sock.getsockname()[1]


@contextlib.contextmanager
def _stub_server(status: int, body: bytes, *, require_auth: bool = False):
    """A throwaway HTTP server standing in for the model server.

    `require_auth=True` answers 401 unless an Authorization header is
    present, mimicking oMLX -- which demands the header but never checks
    its value.
    """

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if require_auth and not self.headers.get("Authorization"):
                reply_status, reply_body = 401, b'{"error": "API key required"}'
            else:
                reply_status, reply_body = status, body
            self.send_response(reply_status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(reply_body)

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("localhost", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://localhost:{server.server_port}"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_check_model_server_alive_returns_none_when_server_responds_ok():
    with _stub_server(200, b'{"data": []}') as base_url:
        assert check_model_server_alive(base_url) is None


def test_check_model_server_alive_raises_when_nothing_is_listening():
    port = _free_port()
    with pytest.raises(ModelServerDown):
        check_model_server_alive(f"http://localhost:{port}")


def test_check_model_server_alive_raises_when_server_returns_non_200():
    with _stub_server(500, b"") as base_url, pytest.raises(ModelServerDown):
        check_model_server_alive(base_url)


def test_check_model_server_alive_sends_an_authorization_header():
    with _stub_server(200, b'{"data": []}', require_auth=True) as base_url:
        assert check_model_server_alive(base_url) is None
