import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from src.auth.conf import settings
from src.auth.models import RefreshToken
from src.auth.repository import AuthRepository
from src.auth.schemas import Token
from src.auth.utils import hash_password, verify_password
from src.models import User


class AuthService:
    def __init__(self, repo: AuthRepository) -> None:
        self.repository = repo

    async def authenticate_user(self, username, password) -> None | User:
        user = await self.repository.find_user(username=username)
        if not user or not verify_password(password, user.password):
            return None
        return user

    def get_access_token(self, user: User) -> str:
        payload = {
            "sub": user.username,
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_IN_MINUTES),
            "typ": "access",
        }
        access_token = jwt.encode(
            payload, key=settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return access_token

    async def get_refresh_token(self, user: User) -> str:
        refresh_token = secrets.token_urlsafe(64)
        hashed = hashlib.sha256(refresh_token.encode()).hexdigest()
        token_data = {
            "token": hashed,
            "user_id": user.id,
            "expires_at": datetime.now(UTC)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRES_IN_DAYS),
        }
        await self.repository.save_refresh_token(token_data)
        return refresh_token

    async def get_tokens(self, user: User) -> Token:
        access_token = self.get_access_token(user)
        refresh_token = await self.get_refresh_token(user)
        await self.repository.set_user_login_time(user)
        return Token(access_token=access_token, refresh_token=refresh_token)

    async def register_user(self, new_user: dict) -> User:
        user_exists = await self.repository.find_user(username=new_user["username"])
        if user_exists:
            return None
        user_exists = await self.repository.find_user(email=new_user["email"])
        if user_exists:
            return None

        hashed_password = hash_password(new_user["password"])
        new_user["password"] = hashed_password
        del new_user["password_confirm"]
        user = await self.repository.create_user(new_user)
        return user

    async def get_token_from_db(self, refresh_token: str) -> RefreshToken:
        hashed = hashlib.sha256(refresh_token.encode()).hexdigest()
        token = await self.repository.get_refresh_token(token=hashed)
        if not token:
            return None

        if token.revoked_at is not None:
            return None

        if token.expires_at.astimezone(UTC) < datetime.now(UTC):
            return None

        return token

    async def refresh(self, refresh_token: str) -> Token:
        token = await self.get_token_from_db(refresh_token)
        user = await self.repository.find_user(id=token.user_id)
        if user is None:
            return None
        access_token = await self.get_tokens(user)
        await self.repository.revoke_token(token)
        return access_token

    async def revoke_token(self, refresh_token: str) -> Token:
        token = await self.get_token_from_db(refresh_token)
        if not token:
            return None
        await self.repository.revoke_token(token)
        return token
