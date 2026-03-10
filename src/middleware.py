import logging
import time
import uuid
from contextvars import ContextVar

from fastapi import FastAPI
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from typing_extensions import Literal

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

logger = logging.getLogger("app.access")


class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Only log HTTP requests (ignore lifespan, websocket, etc.)
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate and store request_id
        rid = uuid.uuid4().hex[:12]
        request_id_ctx.set(rid)

        method = scope["method"]
        path = scope["path"]
        start = time.perf_counter()

        status_code = 500  # default in case send is never called

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                # Inject request-id header into response
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", rid.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "Unhandled exception",
                extra={
                    "request_id": rid,
                    "method": method,
                    "path": path,
                    "status_code": 500,
                    "duration_ms": duration_ms,
                },
            )
            raise
        else:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.info(
                "%s %s → %d (%.2fms)",
                method,
                path,
                status_code,
                duration_ms,
                extra={
                    "request_id": rid,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )


class ProcessTimeMiddleware:
    app: ASGIApp
    time_type_to_multiplier = {
        "ms": 1000.0,
        "s": 1.0,
        "us": 1_000_000.0,
        "ns": 1_000_000_000.0,
    }

    def __init__(
        self,
        app: ASGIApp,
        time_type: Literal["ms", "s", "us", "ns"],
        header_key: str = "X-Process-Time",
    ) -> None:
        self.app = app
        self._multiplier = self.time_type_to_multiplier[time_type]
        self._header_key = header_key

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                process_time = (time.perf_counter() - start_time) * self._multiplier
                headers.append(self._header_key, str(process_time))
            await send(message)

        await self.app(scope, receive, send_wrapper)


def add_middlewares_to_app(app: FastAPI):
    app.add_middleware(ProcessTimeMiddleware, time_type="ms")
    app.add_middleware(LoggingMiddleware)
