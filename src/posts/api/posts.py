from uuid import UUID

from fastapi import APIRouter, Request, status
from fastapi.templating import Jinja2Templates

from src.auth.dependencies import GetCurrentUserDep
from src.core.cache import cache, invalidate_for
from src.posts.dependencies import PostLikeServiceDep, PostServiceDep, TagServiceDep
from src.posts.exceptions import (
    PostAccessDeniedException,
    PostLikeNotFoundException,
    PostNotFoundException,
)
from src.posts.schemas import (
    PostComments,
    PostCreate,
    PostLikeResponse,
    PostResponse,
    PostTagResponse,
    PostUpdate,
    TagResponse,
)

template_router = APIRouter()
api_router = APIRouter()
templates = Jinja2Templates(directory="templates")


@template_router.get("/{post_id}", include_in_schema=False)
async def post_page(
    request: Request,
    post_id: UUID,
    service: PostServiceDep,
    user: GetCurrentUserDep,
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
    user: GetCurrentUserDep,
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
    user: GetCurrentUserDep,
) -> dict:
    post = await service.get_post(id=post_id)
    if not post:
        raise PostNotFoundException
    if post.user_id != user.id:
        raise PostAccessDeniedException
    return post


@api_router.get("/", response_model=list[PostResponse])
@cache(exp=600, namespace="posts", key_params=["user"], response_model=PostResponse)
async def get_posts(service: PostServiceDep, user: GetCurrentUserDep):
    return await service.get_user_posts(user.id)


@api_router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_post(
    post: PostCreate,
    service: PostServiceDep,
    user: GetCurrentUserDep,
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
    user: GetCurrentUserDep,
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
    user: GetCurrentUserDep,
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


@api_router.post(
    "/{post_id}/add_tag/{tag_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=PostTagResponse,
)
async def add_tag_to_post(
    post_id: UUID, tag_id: UUID, service: TagServiceDep, _: GetCurrentUserDep
):
    return await service.add_tag_to_post(tag_id=tag_id, post_id=post_id)


@api_router.get(
    "/{post_id}/tags", status_code=status.HTTP_200_OK, response_model=list[TagResponse]
)
async def get_post_tags(post_id: UUID, service: PostServiceDep, _: GetCurrentUserDep):
    post = await service.get_post(id=post_id)
    if not post:
        raise PostNotFoundException
    return await service.get_post_tags(post_id=post_id)


@api_router.delete("/{post_id}/delete_tag/{tag_id}", status_code=status.HTTP_200_OK)
async def delete_tag_from_post(
    post_id: UUID,
    tag_id: UUID,
    tag_service: TagServiceDep,
    post_service: PostServiceDep,
    user: GetCurrentUserDep,
):
    post = await post_service.get_post(id=post_id)
    if not post:
        raise PostNotFoundException
    if post.user_id != user.id:
        raise PostAccessDeniedException
    await tag_service.delete_tag_from_post(tag_id=tag_id, post_id=post_id)
    return {"message": "successfully deleted"}


@api_router.post(
    "/{post_id}/like",
    response_model=PostLikeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def like_post(
    post_id: UUID, service: PostLikeServiceDep, user: GetCurrentUserDep
):
    return await service.like_post(post_id=post_id, user_id=user.id)


@api_router.delete("/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(
    post_id: UUID, service: PostLikeServiceDep, user: GetCurrentUserDep
):
    post_like = await service.unlike_post(post_id=post_id, user_id=user.id)
    if not post_like:
        raise PostLikeNotFoundException
