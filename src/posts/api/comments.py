from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.auth.dependencies import get_current_user
from src.models import User
from src.posts.dependencies import CommentServiceDep
from src.posts.exceptions import CommentAccessDeniedException, CommentNotFoundException
from src.posts.schemas import CommentCreate, CommentResponse, CommentUpdate

router = APIRouter()


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: UUID,
    service: CommentServiceDep,
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    comment = await service.get_comment(id=comment_id)
    if not comment:
        raise CommentNotFoundException
    if comment.author_id != user.id:
        raise CommentAccessDeniedException
    return comment


@router.get("/", response_model=list[CommentResponse])
async def get_comments(
    service: CommentServiceDep, user: Annotated[User, Depends(get_current_user)]
):
    return await service.get_user_comments(user.id)


@router.post(
    "/",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    comment: CommentCreate,
    service: CommentServiceDep,
    user: Annotated[User, Depends(get_current_user)],
):
    return await service.create_comment(comment, user.id)


@router.put(
    "/{comment_id}", response_model=CommentResponse, status_code=status.HTTP_200_OK
)
async def update_comment(
    comment_id: UUID,
    comment: CommentUpdate,
    service: CommentServiceDep,
    user: Annotated[User, Depends(get_current_user)],
):
    comment = await service.update_comment(comment_id, user.id, comment)
    if not comment:
        raise CommentNotFoundException
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_200_OK)
async def delete_comment(
    comment_id: UUID,
    service: CommentServiceDep,
    user: Annotated[User, Depends(get_current_user)],
):
    comment = await service.delete_comment(comment_id, user.id)
    if not comment:
        raise CommentNotFoundException
    return {"message": "successfully deleted"}
