from typing import Annotated

from fastapi import Depends

from src.db import AsyncSession, get_session
from src.posts.repository import CommentRepository, PostRepository, TagRepository
from src.posts.service import CommentService, PostService, TagService


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


def get_tag_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TagRepository:
    return TagRepository(session=session)


def get_tag_service(
    repository: Annotated[TagRepository, Depends(get_tag_repository)],
) -> TagService:
    return TagService(repo=repository)


PostServiceDep = Annotated[PostService, Depends(get_post_service)]
CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]
TagServiceDep = Annotated[TagService, Depends(get_tag_service)]
