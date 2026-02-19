from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import UUID as PG_UUID
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base, CreatedAt, UpdatedAt

if TYPE_CHECKING:
    from src.auth.models import RefreshToken
    from src.posts.models import Comment, CommentLike, Post, PostLike


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    last_login: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    image_file: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        default=None,
    )

    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    posts: Mapped[list["Post"]] = relationship(back_populates="author")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")
    posts_likes: Mapped[list["PostLike"]] = relationship(back_populates="user")
    comments_likes: Mapped[list["CommentLike"]] = relationship(back_populates="user")

    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"
