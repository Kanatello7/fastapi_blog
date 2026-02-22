from typing import Any

from asyncpg.exceptions import ForeignKeyViolationError, UniqueViolationError
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError

from src.core.exceptions import ForeignKeyConstraintError, UniqueConstraintError
from src.db import AsyncSession


class CRUDRepository:
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
    ) -> list[Any]:
        query = select(self.model)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_one_or_many(self, *filter, **filter_by):
        if not filter and not filter_by:
            raise ValueError("filter cannot be empty")

        query = select(self.model).filter(*filter).filter_by(**filter_by)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, new_data: dict):
        if not new_data:
            raise ValueError("new_data cannot be empty")

        try:
            stmt = insert(self.model).values(**new_data).returning(self.model)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalar_one_or_none()
        except IntegrityError as e:
            await self.session.rollback()
            orig = e.orig.__cause__
            if isinstance(orig, UniqueViolationError):
                raise UniqueConstraintError from e
            if isinstance(orig, ForeignKeyViolationError):
                raise ForeignKeyConstraintError(orig.constraint_name) from e
            raise

    async def update_one_or_more(self, updated_data: dict, **filter_by):
        if not filter_by:
            raise ValueError("filter_by cannot be empty")
        if not updated_data:
            raise ValueError("updated_data cannot be empty")

        updated_post = {k: v for k, v in updated_data.items() if v is not None}
        stmt = (
            update(self.model)
            .values(**updated_post)
            .filter_by(**filter_by)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().all()

    async def delete_one_or_more(self, **filter_by):
        if not filter_by:
            raise ValueError("filter_by cannot be empty")
        stmt = delete(self.model).filter_by(**filter_by).returning(self.model)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().all()
