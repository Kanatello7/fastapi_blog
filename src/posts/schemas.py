from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.users.schemas import UserResponse

# POST


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
    created_at: datetime
    updated_at: datetime
    author: UserResponse
    likes_count: int
    is_liked: bool
    comments_count: int


# COMMENT


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    post_id: UUID
    parent_id: UUID | None = None


class CommentUpdate(CommentBase):
    content: str | None = None


class CommentResponse(CommentBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    post_id: UUID
    parent_id: UUID | None
    created_at: datetime
    updated_at: datetime
    author: UserResponse
    likes_count: int
    is_liked: bool
    replies_count: int


class PostComments(PostBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    author: UserResponse
    comments: list[CommentResponse]


class CommentWithChildren(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    post_id: UUID
    parent_id: UUID | None
    content: str
    created_at: datetime
    updated_at: datetime
    author: UserResponse
    children: list["CommentWithChildren"] = []


# Required for recursive model
CommentWithChildren.model_rebuild()

# TAGS


class TagBase(BaseModel):
    name: str


class TagCreate(TagBase):
    pass


class TagUpdate(TagBase):
    pass


class TagResponse(TagBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slug: str

    created_at: datetime
    updated_at: datetime


class PostTagResponse(BaseModel):
    post_id: UUID
    tag_id: UUID


class PostLikeResponse(BaseModel):
    id: UUID
    post_id: UUID
    user_id: UUID
    created_at: datetime


class CommentLikeResponse(BaseModel):
    id: UUID
    comment_id: UUID
    user_id: UUID
    created_at: datetime
