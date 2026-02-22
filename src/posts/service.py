from uuid import UUID

from slugify import slugify

from src.core.exceptions import ForeignKeyConstraintError, UniqueConstraintError
from src.posts.exceptions import (
    PostLikeNotFoundException,
    PostLikeUniqueViolationException,
    PostNotFoundException,
)
from src.posts.models import Comment, Post, Tag
from src.posts.repository import (
    CommentRepository,
    PostLikeRepository,
    PostRepository,
    TagRepository,
)
from src.posts.schemas import (
    CommentCreate,
    CommentUpdate,
    CommentWithChildren,
    PostCreate,
    PostUpdate,
    TagCreate,
    TagUpdate,
)
from src.users.exceptions import UserNotFoundException


class PostService:
    def __init__(self, repo: PostRepository):
        self.repository = repo

    async def get_post(self, post_id: UUID, user_id: UUID):
        return await self.repository.get_post(post_id=post_id, user_id=user_id)

    async def get_posts(self, user_id: UUID):
        return await self.repository.get_posts(user_id=user_id)

    async def create_post(self, data: PostCreate, user_id: UUID):
        new_data = data.model_dump()
        new_data["user_id"] = user_id
        return await self.repository.create(new_data)

    async def update_post(self, post_id: UUID, user_id: UUID, data: PostUpdate):
        new_data = data.model_dump()
        new_data["user_id"] = user_id
        result = await self.repository.update_one_or_more(
            new_data, id=post_id, user_id=user_id
        )
        return result[0] if result else None

    async def delete_post(self, post_id: UUID, user_id: UUID):
        result = await self.repository.delete_one_or_more(id=post_id, user_id=user_id)
        return result[0] if result else None

    async def get_post_with_comments(self, post_id: UUID):
        result = await self.repository.get_post_with_comments(post_id=post_id)
        return result

    async def get_post_tags(self, post_id: UUID):
        return await self.repository.get_post_tags(post_id=post_id)


class CommentService:
    def __init__(self, repo: CommentRepository):
        self.repository = repo

    async def get_comment(self, *args, **kwargs) -> Comment | None:
        result = await self.repository.get_one_or_many(*args, **kwargs)
        return result[0] if result else None

    async def get_comments(self) -> list[Comment]:
        return await self.repository.get_all()

    async def get_user_comments(self, user_id: UUID):
        return await self.repository.get_user_comments(user_id)

    async def create_comment(self, data: CommentCreate, user_id: UUID):
        new_data = data.model_dump()
        new_data["user_id"] = user_id
        return await self.repository.create(new_data)

    async def update_comment(
        self, comment_id: UUID, user_id: UUID, data: CommentUpdate
    ):
        new_data = data.model_dump()
        new_data["user_id"] = user_id
        result = await self.repository.update_one_or_more(
            new_data, id=comment_id, user_id=user_id
        )
        return result[0] if result else None

    async def delete_comment(self, comment_id: UUID, user_id: UUID):
        result = await self.repository.delete_one_or_more(
            id=comment_id, user_id=user_id
        )
        return result[0] if result else None

    async def get_comments_with_children(self, comment_id: UUID):
        rows = await self.repository.get_comments_with_children(comment_id=comment_id)
        if not rows:
            return None

        nodes: dict[UUID, CommentWithChildren] = {}
        for comment in rows:
            nodes[comment.id] = CommentWithChildren.model_validate(comment)

        root = None
        for node in nodes.values():
            if node.id == comment_id:
                root = node
            elif node.parent_id in nodes:
                nodes[node.parent_id].children.append(node)

        return root


class TagService:
    def __init__(self, repo: TagRepository):
        self.repository = repo

    async def get_tag(self, *args, **kwargs) -> Tag | None:
        result = await self.repository.get_one_or_many(*args, **kwargs)
        return result[0] if result else None

    async def get_tags(self) -> list[Tag]:
        return await self.repository.get_all()

    async def create_tag(self, data: TagCreate):
        new_data = data.model_dump()
        new_data["slug"] = slugify(new_data["name"])
        return await self.repository.create(new_data)

    async def update_tag(self, tag_id: UUID, data: TagUpdate):
        new_data = data.model_dump()
        new_data["slug"] = slugify(new_data["name"])
        result = await self.repository.update_one_or_more(new_data, id=tag_id)
        return result[0] if result else None

    async def delete_tag(self, tag_id: UUID):
        result = await self.repository.delete_one_or_more(id=tag_id)
        return result[0] if result else None

    async def add_tag_to_post(self, tag_id: UUID, post_id: UUID):
        return await self.repository.add_tag_to_post(tag_id=tag_id, post_id=post_id)

    async def delete_tag_from_post(self, tag_id: UUID, post_id: UUID):
        return await self.repository.delete_tag_from_post(
            tag_id=tag_id, post_id=post_id
        )


class PostLikeService:
    def __init__(self, repo: PostLikeRepository):
        self.repo = repo

    async def like_post(self, post_id: UUID, user_id: UUID):
        data = {"post_id": post_id, "user_id": user_id}
        try:
            return await self.repo.create(new_data=data)
        except UniqueConstraintError:
            raise PostLikeUniqueViolationException()
        except ForeignKeyConstraintError as e:
            if e.constraint_name == "post_likes_post_id_fkey":
                raise PostNotFoundException()
            if e.constraint_name == "post_likes_user_id_fkey":
                raise UserNotFoundException()

    async def unlike_post(self, post_id: UUID, user_id: UUID):
        result = await self.repo.delete_one_or_more(post_id=post_id, user_id=user_id)
        if not result:
            raise PostLikeNotFoundException()
        return result[0]
