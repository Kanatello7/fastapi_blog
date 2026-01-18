from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=120)


class UserCreate(UserBase):
    password: str = Field(max_length=50)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    image_file: str | None
    image_path: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
