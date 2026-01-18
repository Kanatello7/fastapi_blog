from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

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
