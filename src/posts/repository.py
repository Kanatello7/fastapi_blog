from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.posts.models import Comment, Post
from src.utils import CRUDRepository


class PostRepository(CRUDRepository):
    model = Post

    async def get_user_posts(self, user_id: UUID) -> list[Post]:
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_post_with_comments(self, post_id: UUID):
        query = (
            select(self.model)
            .where(self.model.id == post_id)
            .options(selectinload(self.model.comments))
        )

        result = await self.session.execute(query)
        return result.scalars().all()


class CommentRepository(CRUDRepository):
    model = Comment

    async def get_user_comments(self, user_id: UUID) -> list[Comment]:
        query = select(self.model).where(self.model.author_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()
