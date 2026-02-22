from uuid import UUID

import asyncpg
from sqlalchemy import delete, exists, func, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased, selectinload

from src.core.utils import CRUDRepository
from src.posts.exceptions import (
    PostNotFoundException,
    PostTagNotFoundException,
    PostTagUniqueViolationException,
    TagNotFoundException,
)
from src.posts.models import Comment, CommentLike, Post, PostLike, PostTag, Tag
from src.users.models import User


class PostRepository(CRUDRepository):
    model = Post

    async def get_post(self, post_id: UUID, user_id: UUID):
        post_likes = (
            select(func.count(PostLike.id))
            .where(PostLike.post_id == post_id)
            .scalar_subquery()
        )
        is_liked = exists().where(
            PostLike.post_id == post_id, PostLike.user_id == user_id
        )
        comments_count = (
            select(func.count(Comment.id))
            .where(Comment.post_id == post_id)
            .scalar_subquery()
        )
        query = (
            select(
                Post,
                post_likes.label("likes_count"),
                is_liked.label("is_liked"),
                comments_count.label("comments_count"),
            )
            .where(Post.id == post_id)
            .options(selectinload(Post.author))
        )
        result = await self.session.execute(query)
        row = result.one_or_none()

        if not row:
            return None

        post, likes_count, is_liked, comments_count = row

        post.likes_count = likes_count
        post.is_liked = is_liked
        post.comments_count = comments_count

        return post

    async def get_posts(self, user_id: UUID) -> list[Post]:
        # Correlated subqueries
        post_likes_count = (
            select(func.count())
            .where(PostLike.post_id == Post.id)
            .correlate(Post)
            .scalar_subquery()
        )

        is_liked = (
            exists()
            .where(PostLike.post_id == Post.id)
            .where(PostLike.user_id == user_id)
            .correlate(Post)
        )

        comments_count = (
            select(func.count())
            .where(Comment.post_id == Post.id)
            .correlate(Post)
            .scalar_subquery()
        )

        # Main query
        stmt = select(
            Post,
            post_likes_count.label("likes_count"),
            is_liked.label("is_liked"),
            comments_count.label("comments_count"),
        ).options(selectinload(Post.author))
        results = await self.session.execute(stmt)
        posts = []
        for row in results.all():
            post = row.Post
            post.likes_count = row.likes_count
            post.is_liked = row.is_liked
            post.comments_count = row.comments_count
            posts.append(post)

        return posts

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

    async def get_comment(self, comment_id: UUID, user_id: UUID):
        likes_count = (
            select(func.count())
            .where(CommentLike.comment_id == comment_id)
            .scalar_subquery()
        )
        is_liked = exists().where(
            CommentLike.comment_id == comment_id, CommentLike.user_id == user_id
        )
        replies_count = (
            select(func.count())
            .where(Comment.parent_id == comment_id)
            .scalar_subquery()
        )
        query = (
            select(
                Comment,
                likes_count.label("likes_count"),
                is_liked.label("is_liked"),
                replies_count.label("replies_count"),
            )
            .where(Comment.id == comment_id)
            .options(selectinload(Comment.author))
        )
        result = await self.session.execute(query)
        row = result.one_or_none()

        if not row:
            return None

        comment, likes_count, is_liked, replies_count = row

        comment.likes_count = likes_count
        comment.is_liked = is_liked
        comment.replies_count = replies_count

        return comment

    async def get_comments(self, user_id: UUID) -> list[Comment]:
        likes_count = (
            select(func.count())
            .where(CommentLike.comment_id == Comment.id)
            .correlate(Comment)
            .scalar_subquery()
        )
        is_liked = (
            exists()
            .where(CommentLike.comment_id == Comment.id, CommentLike.user_id == user_id)
            .correlate(Comment)
        )

        ChildComment = aliased(Comment)
        replies_count = (
            select(func.count())
            .select_from(ChildComment)
            .where(ChildComment.parent_id == Comment.id)
            .correlate(Comment)
            .scalar_subquery()
        )
        query = select(
            Comment,
            likes_count.label("likes_count"),
            is_liked.label("is_liked"),
            replies_count.label("replies_count"),
        ).options(selectinload(Comment.author))

        results = await self.session.execute(query)
        comments = []
        for row in results.all():
            comment = row.Comment
            comment.likes_count = row.likes_count
            comment.is_liked = row.is_liked
            comment.replies_count = row.replies_count
            comments.append(comment)
        return comments

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


class PostLikeRepository(CRUDRepository):
    model = PostLike

    async def get_who_liked(self, post_id: UUID):
        query = (
            select(User.username, User.email, User.id)
            .join(PostLike, PostLike.user_id == User.id)
            .where(PostLike.post_id == post_id)
        )
        results = await self.session.execute(query)
        return results.mappings().all()


class CommentLikeRepository(CRUDRepository):
    model = CommentLike
