from uuid import UUID

from fastapi import APIRouter, status

from src.auth.dependencies import GetCurrentUserDep
from src.core.cache import cache
from src.posts.dependencies import CommentLikeServiceDep, CommentServiceDep
from src.posts.exceptions import CommentAccessDeniedException, CommentNotFoundException
from src.posts.schemas import (
    CommentCreate,
    CommentLikeResponse,
    CommentResponse,
    CommentUpdate,
    CommentWithChildren,
)

router = APIRouter()


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: UUID,
    service: CommentServiceDep,
    user: GetCurrentUserDep,
) -> dict:
    comment = await service.get_comment(comment_id=comment_id, user_id=user.id)
    if not comment:
        raise CommentNotFoundException
    return comment


@router.get("/", response_model=list[CommentResponse])
async def get_user_comments(service: CommentServiceDep, user: GetCurrentUserDep):
    return await service.get_comments(user.id)


@router.post(
    "/",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    comment: CommentCreate,
    service: CommentServiceDep,
    user: GetCurrentUserDep,
):
    return await service.create_comment(comment, user.id)


@router.put(
    "/{comment_id}", response_model=CommentResponse, status_code=status.HTTP_200_OK
)
async def update_comment(
    comment_id: UUID,
    comment: CommentUpdate,
    service: CommentServiceDep,
    user: GetCurrentUserDep,
):
    comment = await service.update_comment(comment_id, user.id, comment)
    if not comment:
        raise CommentNotFoundException
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_200_OK)
async def delete_comment(
    comment_id: UUID,
    service: CommentServiceDep,
    user: GetCurrentUserDep,
):
    comment = await service.delete_comment(comment_id, user.id)
    if not comment:
        raise CommentNotFoundException
    return {"message": "successfully deleted"}


@router.get(
    "/{comment_id}/childrens",
    status_code=status.HTTP_200_OK,
    response_model=CommentWithChildren,
)
@cache(
    exp=300,
    namespace="comments",
    key_params=["comment_id"],
    response_model=CommentWithChildren,
)
async def get_comments_with_childrens(
    comment_id: UUID,
    service: CommentServiceDep,
    _: GetCurrentUserDep,
):
    comment = await service.get_comments_with_children(comment_id=comment_id)
    if not comment:
        raise CommentNotFoundException
    return comment


@router.post(
    "/{comment_id}/like",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentLikeResponse,
)
async def like_comment(
    comment_id: UUID, service: CommentLikeServiceDep, user: GetCurrentUserDep
):
    return await service.like_comment(comment_id=comment_id, user_id=user.id)


@router.delete("/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_comment(
    comment_id: UUID,
    service: CommentLikeServiceDep,
    user: GetCurrentUserDep,
):
    await service.unlike_comment(comment_id=comment_id, user_id=user.id)
