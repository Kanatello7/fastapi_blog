from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.auth.schemas import UserResponse


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str


class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    title: str | None = Field(None, min_length=1, max_length=100)
    content: str | None = None


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    date_posted: datetime
    created_at: datetime
    updated_at: datetime
    author: UserResponse


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    post_id: UUID


class CommentUpdate(CommentBase):
    content: str | None = None


class CommentResponse(CommentBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    author_id: UUID
    post_id: UUID
    created_at: datetime
    updated_at: datetime
