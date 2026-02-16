from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.auth.router import api_router as auth_router
from src.conf import settings
from src.core.cache import RedisError, redis_manager
from src.core.logging_conf import logger
from src.core.rate_limiter import (
    rate_limiter_auth,
    rate_limiter_comments,
    rate_limiter_posts,
)
from src.posts.api.comments import router as api_comments_router
from src.posts.api.posts import api_router as api_posts_router
from src.posts.api.posts import template_router as template_posts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_manager.initialize()
    logger.info("Redis connection open")
    yield
    await redis_manager.close()
    logger.info("Redis connection closed")


app = FastAPI(
    docs_url=None if settings.PRODUCTION else "/docs",
    redoc_url=None if settings.PRODUCTION else "/redoc",
    openapi_url=None if settings.PRODUCTION else "/openapi.json",
    lifespan=lifespan,
)


@app.get("/health/redis", tags=["health"])
async def redis_health():
    try:
        redis = redis_manager.get_client()
        await redis.ping()
        return {"status": "ok"}
    except RedisError:
        raise HTTPException(503, "Redis unavailable")


app.include_router(
    api_posts_router,
    prefix="/api/posts",
    tags=["posts"],
    dependencies=[Depends(rate_limiter_posts)],
)

app.include_router(
    api_comments_router,
    prefix="/api/comments",
    tags=["comments"],
    dependencies=[Depends(rate_limiter_comments)],
)
app.include_router(
    template_posts_router, prefix="/posts", dependencies=[Depends(rate_limiter_posts)]
)

app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["auth"],
    dependencies=[Depends(rate_limiter_auth)],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")


@app.exception_handler(HTTPException)
def general_http_exception_handler(request: Request, exc: HTTPException):
    message = (
        exc.detail
        if exc.detail
        else "An error occured. Please check you request and try again."
    )
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=exc.status_code, content={"detail": message})
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exc.status_code,
            "title": exc.status_code,
            "message": message,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
def request_exception_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/api"):
        errors = [
            {"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": errors},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
