from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    password: str = Field(max_length=50, min_length=8)
    password_confirm: str = Field(max_length=50, min_length=8)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    image_file: str | None
    image_path: str


class FollowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    follower_id: UUID
    following_id: UUID
    created_at: datetime


class UserStatsResponse(BaseModel):
    followers_count: int
    following_count: int
