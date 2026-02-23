from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.db import AsyncSession, get_session
from src.users.exceptions import UserNotFoundException
from src.users.models import User
from src.users.repository import FollowerRepository, UserRepository
from src.users.service import FollowerService, UserService


def get_follower_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> FollowerRepository:
    return FollowerRepository(session=session)


def get_follower_service(
    repo: Annotated[FollowerRepository, Depends(get_follower_repository)],
) -> FollowerService:
    return FollowerService(repo=repo)


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserRepository:
    return UserRepository(session=session)


def get_user_service(
    repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(repo=repo)


FollowerServiceDep = Annotated[FollowerService, Depends(get_follower_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_valid_user(
    user_id: UUID,
    user_service: UserServiceDep,
) -> User:
    user = await user_service.get_user(user_id=user_id)
    if not user:
        raise UserNotFoundException()
    return user


ValidUserDep = Annotated[User, Depends(get_valid_user)]
