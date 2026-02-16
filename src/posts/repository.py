from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.utils import CRUDRepository
from src.posts.models import Comment, Post


class PostRepository(CRUDRepository):
    model = Post

    async def get_user_posts(self, user_id: UUID) -> list[Post]:
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .options(selectinload(Post.author))
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_post_with_comments(self, post_id: UUID):
        query = (
            select(self.model)
            .where(self.model.id == post_id)
            .options(
                selectinload(self.model.comments),
                selectinload(self.model.author),
                selectinload(self.model.comments).selectinload(Comment.author),
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class CommentRepository(CRUDRepository):
    model = Comment

    async def get_user_comments(self, user_id: UUID) -> list[Comment]:
        query = select(self.model).where(self.model.author_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()
