from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.auth.router import api_router as auth_router
from src.conf import settings
from src.posts.router import admin_router as admin_posts_router
from src.posts.router import api_router as api_posts_router
from src.posts.router import template_router as template_posts_router

app = FastAPI(
    docs_url=None if settings.PRODUCTION else "/docs",
    redoc_url=None if settings.PRODUCTION else "/redoc",
    openapi_url=None if settings.PRODUCTION else "/openapi.json", 
)

app.include_router(api_posts_router, prefix="/api/posts", tags=["posts"])
app.include_router(template_posts_router, prefix="/posts")
app.include_router(admin_posts_router, prefix="/api/posts/admin", tags=["admin"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

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
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exc.errors()},
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
