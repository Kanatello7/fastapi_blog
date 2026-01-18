from datetime import date
from uuid import UUID as UID
from uuid import uuid4

from sqlalchemy import UUID, Date, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db import Base, CreatedAt, UpdatedAt


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[UID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(), nullable=False)
    content: Mapped[str] = mapped_column(Text(), nullable=True)
    date_posted: Mapped[date] = mapped_column(Date(), nullable=False, server_default=func.current_date())
    
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]
