from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError

from src.auth.conf import settings
from src.auth.dependencies import AuthRepositoryDep, AuthServiceDep
from src.auth.schemas import RefreshToken, Token, UserCreate, UserResponse
from src.models import User

api_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@api_router.post("/login", response_model=Token)
async def login(
    user_creds: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
):
    user = await service.authenticate_user(user_creds.username, user_creds.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return await service.get_tokens(user)


@api_router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse
)
async def register(new_user: UserCreate, service: AuthServiceDep):
    user = await service.register_user(new_user.model_dump())
    return user

@api_router.post("/refresh", response_model=Token)
async def refresh(req: RefreshToken, service: AuthServiceDep):
    return await service.refresh(req.refresh_token)


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
    except InvalidTokenError:
        raise credentials_exception
    user = await repo.find_user(username=username)
    if user is None:
        raise credentials_exception
    return user


@api_router.get("/check")
async def check_auth(user: Annotated[User, Depends(get_current_user)]):
    return {"status": "authorized", "user": user.username}
