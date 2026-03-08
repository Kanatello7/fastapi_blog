from time import time

from fastapi import FastAPI


class ProcessTimeMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time()

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                print("response.start: ", message)
                duration = time() - start_time
                headers = list(message.get("headers", []))
                headers.append((b"x-process-time", f"{duration:.6f}".encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


def add_middlewares_to_app(app: FastAPI):
    app.add_middleware(ProcessTimeMiddleware)
