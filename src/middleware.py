import logging
import time
import uuid
from contextvars import ContextVar

from fastapi import FastAPI

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
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                headers = list(message.get("headers", []))
                headers.append((b"x-process-time", f"{duration:.6f}".encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


def add_middlewares_to_app(app: FastAPI):
    app.add_middleware(ProcessTimeMiddleware)
    app.add_middleware(LoggingMiddleware)
