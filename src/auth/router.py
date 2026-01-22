from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.dependencies import AuthServiceDep, get_current_user
from src.auth.exceptions import (
    InvalidCredentialsException,
    TokenExpiredException,
    UserExistsException,
)
from src.auth.schemas import RefreshToken, Token, UserCreate, UserResponse
from src.models import User

api_router = APIRouter()


@api_router.post("/login", response_model=Token)
async def login(
    user_creds: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
):
    user = await service.authenticate_user(user_creds.username, user_creds.password)
    if not user:
        raise InvalidCredentialsException

    return await service.get_tokens(user)


@api_router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse
)
async def register(new_user: UserCreate, service: AuthServiceDep):
    user = await service.register_user(new_user.model_dump())
    if not user:
        raise UserExistsException
    return user


@api_router.post("/refresh", response_model=Token)
async def refresh(req: RefreshToken, service: AuthServiceDep):
    token = await service.refresh(req.refresh_token)
    if not token:
        raise TokenExpiredException


@api_router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke(req: RefreshToken, service: AuthServiceDep):
    token = await service.revoke_token(req.refresh_token)
    if not token:
        raise TokenExpiredException


@api_router.get("/check")
async def check_auth(user: Annotated[User, Depends(get_current_user)]):
    return {"status": "authorized", "user": user.username}
