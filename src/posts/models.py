from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import UUID as PG_UUID
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base, CreatedAt, UpdatedAt

if TYPE_CHECKING:
    from src.users.models import User


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(), nullable=False)
    content: Mapped[str] = mapped_column(Text(), nullable=True)

    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    author: Mapped["User"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post")
    tags: Mapped[list["Tag"]] = relationship(
        secondary="post_tags", back_populates="posts"
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(String(), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(), unique=True, nullable=False, index=True)

    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]
    posts: Mapped[list["Post"]] = relationship(
        secondary="post_tags", back_populates="tags"
    )


class PostTag(Base):
    __tablename__ = "post_tags"

    post_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    post_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("comments.id"),
        nullable=True,
        index=True,
    )

    content: Mapped[str] = mapped_column(Text(), nullable=False)

    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    author: Mapped["User"] = relationship(back_populates="comments")
    post: Mapped["Post"] = relationship(back_populates="comments")
