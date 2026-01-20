from typing import Annotated

from fastapi import Depends

from src.db import AsyncSession, get_session
from src.posts.repository import PostRepository
from src.posts.service import PostService


def get_repository(session: Annotated[AsyncSession, Depends(get_session)]):
    return PostRepository(session=session)

def get_service(repo: Annotated[PostRepository, Depends(get_repository)]):
    return PostService(repo=repo)

PostServiceDep = Annotated[PostService, Depends(get_service)]
PostRepositoryDep = Annotated[PostRepository, Depends(get_repository)]


