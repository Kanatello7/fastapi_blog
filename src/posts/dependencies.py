from typing import Annotated

from fastapi import Depends

from src.db import AsyncSession, get_session
from src.posts.repository import CommentRepository, PostRepository
from src.posts.service import CommentService, PostService


def get_post_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PostRepository:
    return PostRepository(session=session)


def get_post_service(
    repo: Annotated[PostRepository, Depends(get_post_repository)],
) -> PostService:
    return PostService(repo=repo)


def get_comment_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CommentRepository:
    return CommentRepository(session=session)


def get_comment_service(
    repo: Annotated[CommentRepository, Depends(get_comment_repository)],
) -> CommentService:
    return CommentService(repo=repo)


PostServiceDep = Annotated[PostService, Depends(get_post_service)]
CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]
