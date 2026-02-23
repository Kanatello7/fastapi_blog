from typing import Annotated

from fastapi import Depends

from src.db import AsyncSession, get_session
from src.users.repository import FollowerRepository
from src.users.service import FollowerService


def get_follower_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FollowerRepository:
    return FollowerRepository(session=session)


def get_follower_service(
    repo: Annotated[FollowerRepository, Depends(get_follower_repository)],
) -> FollowerService:
    return FollowerService(repo=repo)


FollowerServiceDep = Annotated[FollowerService, Depends(get_follower_service)]
