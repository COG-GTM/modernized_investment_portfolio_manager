"""Ephemeral in-process server used by the replay tool and the retry-safety check.

Runs the batch router alone under uvicorn in a background thread against the configured
SQLite file, so a "service restart" is a real new server process-state on the same database.
"""
import socket
import threading
import time

import uvicorn
from fastapi import FastAPI

from techfest_batch.db import ensure_schema
from techfest_batch.router import router


def create_app() -> FastAPI:
    app = FastAPI(title="Batch Completion Service (synthetic demonstration)")
    app.include_router(router)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class EphemeralServer:
    def __init__(self, port: int | None = None):
        self.port = port or free_port()
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self, wait_s: float = 10.0) -> "EphemeralServer":
        ensure_schema()
        config = uvicorn.Config(create_app(), host="127.0.0.1", port=self.port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        deadline = time.monotonic() + wait_s
        while time.monotonic() < deadline:
            if self._server.started:
                return self
            time.sleep(0.05)
        raise RuntimeError("ephemeral batch server did not start")

    def stop(self, wait_s: float = 10.0) -> None:
        if self._server is None:
            return
        self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=wait_s)
        self._server = None
        self._thread = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
