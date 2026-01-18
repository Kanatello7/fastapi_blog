from typing import Annotated

from fastapi import Depends

from src.auth.repository import AuthRepository
from src.auth.service import AuthService
from src.db import AsyncSession, get_session


def get_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthRepository:
    return AuthRepository(session=session)


def get_service(
    repo: Annotated[AuthRepository, Depends(get_repository)],
) -> AuthService:
    return AuthService(repo=repo)


AuthServiceDep = Annotated[AuthService, Depends(get_service)]
AuthRepositoryDep = Annotated[AuthRepository, Depends(get_repository)]
