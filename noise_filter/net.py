"""HTTPS for the app's few online features (noise sample upload, model updates).

Two things go wrong on real Windows PCs that never show up on a developer machine:

  - Python checks certificates against the roots it can list from the Windows store, but Windows
    only downloads many roots the first time something asks for them. A fresh PC can therefore
    fail with CERTIFICATE_VERIFY_FAILED although the browser opens the same site fine. We verify
    through Windows itself (the `truststore` package) and fall back to Mozilla's roots (`certifi`).
  - urllib's errors are cryptic ("HTTP Error 400: Bad Request", "[Errno 11001] getaddrinfo
    failed"). NetError carries a short reason key the UI can translate, plus the detail.
"""
from __future__ import annotations

import json
import socket
import ssl
import time
import urllib.error
import urllib.request

REASONS = ["offline", "timeout", "tls", "blocked", "rate_limited", "rejected", "server"]


class NetError(RuntimeError):
    """`reason` is one of REASONS; str(e) is the technical detail (English, for bug reports)."""

    def __init__(self, reason: str, detail: str = "", status: int | None = None):
        super().__init__(detail or reason)
        self.reason, self.status = reason, status


def _contexts():
    """SSL contexts to try, best first."""
    try:
        import truststore                            # verifies with the OS (Windows CryptoAPI)
        yield truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    except Exception:
        pass
    yield ssl.create_default_context()
    try:
        import certifi
        yield ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass


def _is_tls_error(e: BaseException) -> bool:
    r = getattr(e, "reason", e)
    return isinstance(r, ssl.SSLError) or isinstance(e, ssl.SSLError)


def _error_detail(e: urllib.error.HTTPError) -> str:
    try:
        body = e.read(4096)
        msg = json.loads(body).get("error")
        if msg:
            return f"HTTP {e.code}: {msg}"
    except Exception:
        pass
    return f"HTTP {e.code} {e.reason}"


def classify(e: BaseException) -> NetError:
    if isinstance(e, NetError):
        return e
    if isinstance(e, urllib.error.HTTPError):
        detail = _error_detail(e)
        if e.code == 429:
            return NetError("rate_limited", detail, 429)
        if e.code in (400, 404, 405, 411, 413, 415, 422):
            return NetError("rejected", detail, e.code)
        if e.code in (401, 403, 407, 451):           # school / office web filter or proxy
            return NetError("blocked", detail, e.code)
        return NetError("server", detail, e.code)
    if _is_tls_error(e):
        return NetError("tls", str(getattr(e, "reason", e)))
    r = getattr(e, "reason", e)
    if isinstance(r, (socket.timeout, TimeoutError)) or isinstance(e, (socket.timeout, TimeoutError)):
        return NetError("timeout", str(r))
    if isinstance(r, socket.gaierror):
        return NetError("offline", f"DNS: {r}")
    if isinstance(r, (ConnectionResetError, ConnectionAbortedError)):
        return NetError("blocked", str(r))              # often a firewall cutting the connection
    return NetError("offline", str(r))


def request(req: urllib.request.Request, timeout: float = 30.0, limit: int = 64 * 1024,
            retries: int = 2) -> bytes:
    """Open `req` and return the body (at most `limit` bytes). Raises NetError.

    Certificate errors are retried with the next trust store; timeouts, dropped connections and
    5xx answers are retried a few times with a short pause; 429 waits a little longer."""
    last: NetError | None = None
    contexts = list(_contexts())
    ci = 0
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=contexts[ci]) as r:
                return r.read(limit)
        except Exception as e:
            last = classify(e)
        if last.reason == "tls" and ci + 1 < len(contexts):
            ci += 1
            continue
        if last.reason in ("timeout", "server", "rate_limited", "blocked") and attempt < retries:
            if last.reason == "blocked" and last.status:   # a real 403 page will not change
                raise last
            attempt += 1
            time.sleep(20 * attempt if last.reason == "rate_limited" else 2 * attempt)
            continue
        raise last
