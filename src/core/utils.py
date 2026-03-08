from typing import Any, Dict, Generic, Optional, TypeVar, Union, get_args

from asyncpg.exceptions import ForeignKeyViolationError, UniqueViolationError
from pydantic import BaseModel
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError

from src.core.exceptions import ForeignKeyConstraintError, UniqueConstraintError
from src.db import AsyncSession

CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class CRUDRepository(Generic[CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    model = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for base in getattr(cls, "__orig_bases__", []):
            args = get_args(base)
            if args and len(args) == 3:
                cls._create_schema = args[0]
                cls._update_schema = args[1]
                cls._response_schema = args[2]
                break

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
    ) -> list[ResponseSchemaType]:
        query = select(self.model)
        result = await self.session.execute(query)
        return [
            self._response_schema.model_validate(obj, from_attributes=True)
            for obj in result.scalars().all()
        ]

    async def get_one_or_many(self, *filter, **filter_by) -> list[ResponseSchemaType]:
        if not filter and not filter_by:
            raise ValueError("filter cannot be empty")

        query = select(self.model).filter(*filter).filter_by(**filter_by)
        result = await self.session.execute(query)
        return [
            self._response_schema.model_validate(obj, from_attributes=True)
            for obj in result.scalars().all()
        ]

    async def create(
        self, data: Union[CreateSchemaType, Dict[str, Any]]
    ) -> Optional[ResponseSchemaType]:
        if not data:
            raise ValueError("new_data cannot be empty")

        if isinstance(data, dict):
            new_data = data
        else:
            new_data = data.model_dump(exclude_unset=True)

        try:
            stmt = insert(self.model).values(**new_data).returning(self.model)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return self._response_schema.model_validate(
                result.scalar_one_or_none(), from_attributes=True
            )
        except IntegrityError as e:
            await self.session.rollback()
            orig = e.orig.__cause__
            if isinstance(orig, UniqueViolationError):
                raise UniqueConstraintError from e
            if isinstance(orig, ForeignKeyViolationError):
                raise ForeignKeyConstraintError(orig.constraint_name) from e
            raise

    async def update_one_or_more(
        self, data: Union[UpdateSchemaType, Dict[str, Any]], **filter_by
    ) -> list[ResponseSchemaType]:
        if not filter_by:
            raise ValueError("filter_by cannot be empty")
        if not data:
            raise ValueError("updated_data cannot be empty")

        if isinstance(data, dict):
            updated_data = data
        else:
            updated_data = data.model_dump(exclude_unset=True)

        updated_post = {k: v for k, v in updated_data.items() if v is not None}
        stmt = (
            update(self.model)
            .values(**updated_post)
            .filter_by(**filter_by)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return [
            self._response_schema.model_validate(obj, from_attributes=True)
            for obj in result.scalars().all()
        ]

    async def delete_one_or_more(self, **filter_by) -> list[ResponseSchemaType]:
        if not filter_by:
            raise ValueError("filter_by cannot be empty")
        stmt = delete(self.model).filter_by(**filter_by).returning(self.model)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return [
            self._response_schema.model_validate(obj, from_attributes=True)
            for obj in result.scalars().all()
        ]
