from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates

from src.auth.dependencies import get_current_user, require_admin
from src.models import User
from src.posts.dependencies import PostServiceDep
from src.posts.schemas import PostCreate, PostResponse, PostUpdate

template_router = APIRouter()
api_router = APIRouter()
templates = Jinja2Templates(directory="templates")


## Admin routes
@api_router.get("/all", response_model=list[PostResponse])
async def get_all_posts(service: PostServiceDep, user: Annotated[User, Depends(require_admin)]):
    return await service.get_posts()


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

@api_router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(post: PostCreate, service: PostServiceDep, user: Annotated[User, Depends(get_current_user)]):
    new_post_data = post.model_dump()
    new_post_data["user_id"] = user.id
    new_post = await service.create_post(new_post_data)
    return new_post

@api_router.put(
    "/{post_id}",
    response_model=PostResponse,
    status_code=status.HTTP_200_OK
)
async def update_post(post_id: UUID, post: PostUpdate, service: PostServiceDep, user: Annotated[User, Depends(get_current_user)]):
    new_post_data = post.model_dump()
    new_post_data["user_id"] = user.id
    new_post = await service.update_post(post_id, new_post_data)
    return new_post


@api_router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_post(post_id: UUID, service: PostServiceDep, user: Annotated[User, Depends(get_current_user)]):
    await service.delete_post(post_id, user.id)