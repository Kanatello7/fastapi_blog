from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates

from src.auth.dependencies import get_current_user
from src.models import User
from src.posts.dependencies import PostServiceDep
from src.posts.schemas import PostCreate, PostResponse

template_router = APIRouter()
api_router = APIRouter()
templates = Jinja2Templates(directory="templates")

@template_router.get("/{post_id}", include_in_schema=False)
async def post_page(request: Request, post_id: UUID, service: PostServiceDep, user: Annotated[User, Depends(get_current_user)]):
    post = await service.get_post(id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail="you don't have access to this post")
    return templates.TemplateResponse(
        request, "post.html", {"post": post, "title": post.title}
    )


@template_router.get("/", include_in_schema=False, name="home")
@template_router.get("/", include_in_schema=False, name="posts")
async def home(request: Request, service: PostServiceDep, user: Annotated[User, Depends(get_current_user)]) -> str:
    posts = await service.get_user_posts(user.id)
    return templates.TemplateResponse(
        request, "home.html", {"posts": posts, "title": "Home"}
    )


@api_router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: UUID, service: PostServiceDep, user: Annotated[User, Depends(get_current_user)]) -> dict:
    post = await service.get_post(id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != user.id:
        raise HTTPException(status_code=403, detail="you don't have access to this post")
    return post

@api_router.get("/", response_model=list[PostResponse])
async def get_posts(service: PostServiceDep, user: Annotated[User, Depends(get_current_user)]):
    return await service.get_user_posts(user.id)


# @api_router.post(
#     "/",
#     response_model=PostResponse,
#     status_code=status.HTTP_201_CREATED,
# )
# def create_post(post: PostCreate):
#     new_id = max(p["id"] for p in posts) + 1 if posts else 1
#     new_post = {
#         "id": new_id,
#         "author": post.author,
#         "title": post.title,
#         "content": post.content,
#         "date_posted": "April 23, 2025",
#     }
#     posts.routerend(new_post)
#     return new_post
