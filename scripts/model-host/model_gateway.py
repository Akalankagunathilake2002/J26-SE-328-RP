"""Access-key gateway in front of the models that run on this Mac, for a SkillBridge server elsewhere.

mlx_lm.server (Gemma, port 8082) and the avatar engine (port 8768) have no authentication, so they stay on
127.0.0.1 and this gateway is the only thing the tunnel exposes:

    /llm/...     -> http://127.0.0.1:8082/...   (LOCAL_LLM_URL=https://<tunnel>/llm)
    /avatar/...  -> http://127.0.0.1:8768/...   (LOCAL_AVATAR_URL=https://<tunnel>/avatar)
    /health      -> which models are up

Every request needs "Authorization: Bearer <key>" (the services send MODEL_HOST_KEY). Responses are streamed,
and Range headers pass through so avatar videos can seek. Standard library only.

    MODEL_HOST_KEY=... python3 scripts/model-host/model_gateway.py [--port 8090]
"""
import argparse
import hmac
import http.client
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAMS = {"llm": ("127.0.0.1", 8082), "avatar": ("127.0.0.1", 8768)}
FORWARD_REQUEST = ("content-type", "range", "accept")
FORWARD_RESPONSE = ("content-type", "content-length", "content-range", "accept-ranges", "last-modified", "etag")
MAX_BODY = 10 * 2 ** 20
TIMEOUT = 300                       # long LLM generations (lessons) take up to a minute or two

KEY = os.environ.get("MODEL_HOST_KEY", "")


def upstream_up(host: str, port: int) -> bool:
    try:
        conn = http.client.HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/")
        conn.getresponse().read()
        return True
    except OSError:
        return False


class Gateway(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[gateway] {self.address_string()} {fmt % args}\n")

    def _reply(self, status: int, body: dict):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _authorised(self) -> bool:
        given = self.headers.get("Authorization", "")
        return bool(KEY) and hmac.compare_digest(given.encode(), f"Bearer {KEY}".encode())

    def _handle(self):
        if not self._authorised():
            return self._reply(401, {"detail": "Missing or wrong model host key"})
        name, _, rest = self.path.lstrip("/").partition("/")
        if name == "health":
            return self._reply(200, {n: upstream_up(*hp) for n, hp in UPSTREAMS.items()})
        if name not in UPSTREAMS:
            return self._reply(404, {"detail": "Use /llm/... or /avatar/..."})
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            return self._reply(413, {"detail": "Request body too large"})
        body = self.rfile.read(length) if length else None
        headers = {k: v for k, v in self.headers.items() if k.lower() in FORWARD_REQUEST}
        try:
            conn = http.client.HTTPConnection(*UPSTREAMS[name], timeout=TIMEOUT)
            conn.request(self.command, "/" + rest, body=body, headers=headers)
            res = conn.getresponse()
        except OSError as e:
            return self._reply(503, {"detail": f"{name} is not running on the model host: {e}"})
        self.send_response(res.status)
        for k, v in res.getheaders():
            if k.lower() in FORWARD_RESPONSE:
                self.send_header(k, v)
        chunked = res.getheader("Content-Length") is None
        if chunked:
            self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        while chunk := res.read(64 * 1024):
            if chunked:
                self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
            else:
                self.wfile.write(chunk)
        if chunked:
            self.wfile.write(b"0\r\n\r\n")
        conn.close()

    do_GET = do_POST = do_HEAD = _handle


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()
    if len(KEY) < 24:
        sys.exit("Set MODEL_HOST_KEY to a long random value (start-model-host.sh makes one).")
    print(f"[gateway] http://127.0.0.1:{args.port}  /llm -> :8082  /avatar -> :8768", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Gateway).serve_forever()


if __name__ == "__main__":
    main()
