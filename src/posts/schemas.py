from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.auth.schemas import UserResponse


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str


class PostCreate(PostBase):
    user_id: UUID


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: UUID
    date_posted: datetime
    author: UserResponse
