from uuid import UUID

import asyncpg
from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from src.core.utils import CRUDRepository
from src.posts.exceptions import (
    PostNotFoundException,
    PostTagNotFoundException,
    PostTagUniqueViolationException,
    TagNotFoundException,
)
from src.posts.models import Comment, Post, PostTag, Tag


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

    async def get_post_tags(self, post_id: UUID):
        query = (
            select(Tag)
            .join(PostTag, Tag.id == PostTag.tag_id)
            .where(PostTag.post_id == post_id)
        )
        result = await self.session.execute(query)
        return result.scalars().all()


class CommentRepository(CRUDRepository):
    model = Comment

    async def get_user_comments(self, user_id: UUID) -> list[Comment]:
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_comments_with_children(self, comment_id: UUID):
        # level literal(1).label("level")
        # Base case
        anchor = select(Comment.id).where(Comment.id == comment_id)
        comments_cte = anchor.cte(name="comments_cte", recursive=True)

        recursive = select(Comment.id).join(
            comments_cte, Comment.parent_id == comments_cte.c.id
        )
        comments_cte = comments_cte.union_all(recursive)

        # Join back to get full objects while preserving CTE logic
        final_query = (
            select(Comment)
            .join(comments_cte, Comment.id == comments_cte.c.id)
            .options(selectinload(Comment.author))
        )

        result = await self.session.execute(final_query)
        return result.scalars().all()


class TagRepository(CRUDRepository):
    model = Tag

    async def add_tag_to_post(self, tag_id: UUID, post_id: UUID):
        stmt = insert(PostTag).values(tag_id=tag_id, post_id=post_id).returning(PostTag)
        try:
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.scalar_one()
        except IntegrityError as e:
            await self.session.rollback()
            orig = e.orig.__cause__
            if isinstance(orig, asyncpg.exceptions.UniqueViolationError):
                raise PostTagUniqueViolationException from e
            if isinstance(orig, asyncpg.exceptions.ForeignKeyViolationError):
                constraint = orig.constraint_name 

                if constraint == "post_tags_post_id_fkey":
                    raise PostNotFoundException from e 
                if constraint == "post_tags_tag_id_fkey":
                    raise TagNotFoundException from e
            raise 
        
    async def delete_tag_from_post(self, tag_id: UUID, post_id: UUID):
        stmt = (
            delete(PostTag)
            .where(PostTag.tag_id == tag_id, PostTag.post_id == post_id)
            .returning(PostTag)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            raise PostTagNotFoundException
        await self.session.commit()
        return row
        