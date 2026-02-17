from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from src.auth.conf import settings
from src.auth.repository import AuthRepository
from src.auth.service import AuthService
from src.db import AsyncSession, get_session
from src.users.models import User


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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], repo: AuthRepositoryDep
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        if payload.get("typ") != "access":
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except InvalidTokenError:
        raise credentials_exception
    user = await repo.find_user(username=username)
    if user is None:
        raise credentials_exception
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403)
    return user


RequireAdminDep = Annotated[User, Depends(require_admin)]
GetCurrentUserDep = Annotated[User, Depends(get_current_user)]
