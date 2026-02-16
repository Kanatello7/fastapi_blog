from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.templating import Jinja2Templates

from src.auth.dependencies import get_current_user
from src.core.cache import cache, invalidate_for
from src.posts.dependencies import PostServiceDep
from src.posts.exceptions import PostAccessDeniedException, PostNotFoundException
from src.posts.schemas import PostComments, PostCreate, PostResponse, PostUpdate
from src.users.models import User

template_router = APIRouter()
api_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@template_router.get("/{post_id}", include_in_schema=False)
async def post_page(
    request: Request,
    post_id: UUID,
    service: PostServiceDep,
    user: Annotated[User, Depends(get_current_user)],
):
    post = await service.get_post(id=post_id)
    if not post:
        raise PostNotFoundException
    if post.user_id != user.id:
        raise PostAccessDeniedException
    return templates.TemplateResponse(
        request, "post.html", {"post": post, "title": post.title}
    )


@template_router.get("/", include_in_schema=False, name="home")
async def home(
    request: Request,
    service: PostServiceDep,
    user: Annotated[User, Depends(get_current_user)],
) -> str:
    posts = await service.get_user_posts(user.id)
    return templates.TemplateResponse(
        request, "home.html", {"posts": posts, "title": "Home"}
    )


@api_router.get("/{post_id}", response_model=PostResponse)
@cache(
    exp=300,
    namespace="post",
    key_params=["post_id", "user"],
    response_model=PostResponse,
)
async def get_post(
    post_id: UUID,
    service: PostServiceDep,
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    post = await service.get_post(id=post_id)
    if not post:
        raise PostNotFoundException
    if post.user_id != user.id:
        raise PostAccessDeniedException
    return post


@api_router.get("/", response_model=list[PostResponse])
@cache(exp=600, namespace="posts", key_params=["user"], response_model=PostResponse)
async def get_posts(
    service: PostServiceDep, user: Annotated[User, Depends(get_current_user)]
):
    return await service.get_user_posts(user.id)


@api_router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    post: PostCreate,
    service: PostServiceDep,
    user: Annotated[User, Depends(get_current_user)],
):
    post = await service.create_post(post, user.id)
    await invalidate_for(get_posts, user=user)
    return post


@api_router.put(
    "/{post_id}", response_model=PostResponse, status_code=status.HTTP_200_OK
)
async def update_post(
    post_id: UUID,
    post: PostUpdate,
    service: PostServiceDep,
    user: Annotated[User, Depends(get_current_user)],
):
    post = await service.update_post(post_id, user.id, post)
    if not post:
        raise PostNotFoundException
    await invalidate_for(
        get_posts,
        get_post,
        post_with_comments,
        user=user,
        post_id=post_id,
    )
    return post


@api_router.delete("/{post_id}", status_code=status.HTTP_200_OK)
async def delete_post(
    post_id: UUID,
    service: PostServiceDep,
    user: Annotated[User, Depends(get_current_user)],
):
    post = await service.delete_post(post_id, user.id)
    if not post:
        raise PostNotFoundException
    await invalidate_for(
        get_posts,
        get_post,
        post_with_comments,
        user=user,
        post_id=post_id,
    )
    return {"message": "successfully deleted"}


@api_router.get(
    "/{post_id}/comments", status_code=status.HTTP_200_OK, response_model=PostComments
)
@cache(
    exp=300,
    namespace="post_with_comments",
    key_params=["post_id"],
    response_model=PostComments,
)
async def post_with_comments(post_id: UUID, service: PostServiceDep):
    post = await service.get_post_with_comments(post_id)
    if not post:
        raise PostNotFoundException
    return post
