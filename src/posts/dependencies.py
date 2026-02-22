from typing import Annotated

from fastapi import Depends

from src.db import AsyncSession, get_session
from src.posts.repository import (
    CommentLikeRepository,
    CommentRepository,
    PostLikeRepository,
    PostRepository,
    TagRepository,
)
from src.posts.service import (
    CommentLikeService,
    CommentService,
    PostLikeService,
    PostService,
    TagService,
)


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


def get_post_like_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PostLikeRepository:
    return PostLikeRepository(session=session)


def get_post_like_service(
    repository: Annotated[PostLikeRepository, Depends(get_post_like_repository)],
) -> PostLikeService:
    return PostLikeService(repo=repository)


def get_comment_like_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CommentLikeRepository:
    return CommentLikeRepository(session=session)


def get_comment_like_service(
    repository: Annotated[CommentLikeRepository, Depends(get_comment_like_repository)],
) -> CommentLikeService:
    return CommentLikeService(repo=repository)


PostServiceDep = Annotated[PostService, Depends(get_post_service)]
CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]
TagServiceDep = Annotated[TagService, Depends(get_tag_service)]
PostLikeServiceDep = Annotated[PostLikeService, Depends(get_post_like_service)]
CommentLikeServiceDep = Annotated[CommentLikeService, Depends(get_comment_like_service)]
