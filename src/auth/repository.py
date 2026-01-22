from datetime import UTC, datetime

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import RefreshToken
from src.models import User
from src.posts.models import Post


class AuthRepository:
    model = User

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_user(self, *args, **kwargs) -> User:
        query = select(self.model).filter(*args).filter_by(**kwargs).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, data: dict) -> User:
        new_user = self.model(**data)
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user
        # Core Style
        # stmt = insert(self.model).values(**data).returning(self.model)
        # result = await self.session.execute(stmt)
        # return result.scalar_one()

    async def save_refresh_token(self, token_data: dict) -> RefreshToken:
        new_token = RefreshToken(**token_data)
        self.session.add(new_token)
        await self.session.commit()
        await self.session.refresh(new_token)
        return new_token
        # Core Style
        # stmt = insert(self.model).values(**token_data).returning(self.model)
        # result = await self.session.execute(stmt)
        # return result.scalar_one()
    
    async def get_refresh_token(self, *args, **kwargs) -> RefreshToken:
        query = select(RefreshToken).filter(*args).filter_by(**kwargs).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def revoke_token(self, token: RefreshToken) -> RefreshToken:
        token.revoked_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(token)
        return token
    
    async def set_user_login_time(self, user: User):
        user.last_login = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(user)
        