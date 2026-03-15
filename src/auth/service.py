import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from src.auth.conf import settings
from src.auth.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    TokenExpiredException,
    UserExistsException,
)
from src.auth.metrics import (
    AUTH_ERRORS_TOTAL,
    AUTH_REQUESTS_TOTAL,
    AUTH_SUCCESS_LOGINS_TOTAL,
    USER_CREATION_ERRORS_TOTAL,
)
from src.auth.models import RefreshToken
from src.auth.repository import AuthRepository
from src.auth.schemas import Token
from src.users.models import User


class AuthService:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    def __init__(self, repo: AuthRepository) -> None:
        self.repository = repo

    async def authenticate_user(self, username: str, password: str) -> User:
        AUTH_REQUESTS_TOTAL.labels(endpoint="/api/auth/login", method="POST").inc()
        user = await self.repository.find_user(username=username)
        if not user or not self.verify_password(password, user.password):
            AUTH_ERRORS_TOTAL.labels(
                endpoint="/api/auth/login", error_type="invalid_credentials"
            ).inc()
            raise InvalidCredentialsException
        return user

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def _create_access_token(self, user: User) -> str:
        payload = {
            "sub": user.username,
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES_IN_MINUTES),
            "typ": "access",
        }
        return jwt.encode(
            payload, key=settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )

    async def _create_refresh_token(self, user: User) -> str:
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

    async def _create_token_pair(self, user: User) -> Token:
        access_token = self._create_access_token(user)
        refresh_token = await self._create_refresh_token(user)
        return Token(access_token=access_token, refresh_token=refresh_token)

    async def login(self, user: User) -> Token:
        try:
            tokens = await self._create_token_pair(user)
            await self.repository.set_user_login_time(user)
            AUTH_SUCCESS_LOGINS_TOTAL.inc()
            return tokens
        except Exception:
            AUTH_ERRORS_TOTAL.labels(
                endpoint="/api/auth/login", error_type="internal"
            ).inc()
            raise

    async def register_user(self, new_user: dict) -> User:
        AUTH_REQUESTS_TOTAL.labels(endpoint="/api/auth/register", method="POST").inc()

        user_exists = await self.repository.find_user(username=new_user["username"])
        if user_exists:
            USER_CREATION_ERRORS_TOTAL.labels(error_type="username_exists").inc()
            raise UserExistsException

        user_exists = await self.repository.find_user(email=new_user["email"])
        if user_exists:
            USER_CREATION_ERRORS_TOTAL.labels(error_type="email_exists").inc()
            raise UserExistsException

        try:
            hashed_password = self.hash_password(new_user["password"])
            new_user["password"] = hashed_password
            del new_user["password_confirm"]
            user = await self.repository.create_user(new_user)
            return user
        except Exception:
            USER_CREATION_ERRORS_TOTAL.labels(error_type="internal").inc()
            raise

    async def _get_valid_refresh_token(self, refresh_token: str) -> RefreshToken | None:
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
        AUTH_REQUESTS_TOTAL.labels(endpoint="/api/auth/refresh", method="POST").inc()

        token = await self._get_valid_refresh_token(refresh_token)
        if token is None:
            AUTH_ERRORS_TOTAL.labels(
                endpoint="/api/auth/refresh", error_type="invalid_token"
            ).inc()
            raise InvalidTokenException

        user = await self.repository.find_user(id=token.user_id)
        if user is None:
            AUTH_ERRORS_TOTAL.labels(
                endpoint="/api/auth/refresh", error_type="user_not_found"
            ).inc()
            raise TokenExpiredException

        try:
            tokens = await self._create_token_pair(user)
            await self.repository.revoke_token(token)
            return tokens
        except (InvalidTokenException, TokenExpiredException):
            raise
        except Exception:
            AUTH_ERRORS_TOTAL.labels(
                endpoint="/api/auth/refresh", error_type="internal"
            ).inc()
            raise

    async def revoke_token(self, refresh_token: str) -> RefreshToken:
        AUTH_REQUESTS_TOTAL.labels(endpoint="/api/auth/revoke", method="POST").inc()

        token = await self._get_valid_refresh_token(refresh_token)
        if not token:
            AUTH_ERRORS_TOTAL.labels(
                endpoint="/api/auth/revoke", error_type="invalid_token"
            ).inc()
            raise TokenExpiredException

        try:
            await self.repository.revoke_token(token)
            return token
        except (TokenExpiredException,):
            raise
        except Exception:
            AUTH_ERRORS_TOTAL.labels(
                endpoint="/api/auth/revoke", error_type="internal"
            ).inc()
            raise
