from uuid import UUID

from src.posts.models import Comment, Post
from src.posts.repository import CommentRepository, PostRepository
from src.posts.schemas import (
    CommentCreate,
    CommentUpdate,
    CommentWithChildren,
    PostCreate,
    PostUpdate,
)


class PostService:
    def __init__(self, repo: PostRepository):
        self.repository = repo

    async def get_post(self, *args, **kwargs) -> Post | None:
        result = await self.repository.get_one_or_many(*args, **kwargs)
        return result[0] if result else None

    async def get_posts(self) -> list[Post]:
        return await self.repository.get_all()

    async def get_user_posts(self, user_id: UUID):
        return await self.repository.get_user_posts(user_id)

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
