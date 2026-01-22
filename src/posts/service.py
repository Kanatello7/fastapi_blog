from uuid import UUID

from src.posts.models import Post
from src.posts.repository import PostRepository
from src.posts.schemas import PostCreate, PostUpdate


class PostService:
    def __init__(self, repo: PostRepository):
        self.repository = repo

    async def get_post(self, *args, **kwargs) -> Post:
        return await self.repository.get_post(*args, **kwargs)

    async def get_posts(self) -> list[Post]:
        return await self.repository.get_posts()

    async def get_user_posts(self, user_id: UUID):
        return await self.repository.get_user_posts(user_id)

    async def create_post(self, data: PostCreate, user_id: UUID):
        new_data = data.model_dump()
        new_data["user_id"] = user_id
        return await self.repository.create_post(new_data)

    async def update_post(self, post_id: UUID, user_id: UUID, data: PostUpdate):
        new_data = data.model_dump()
        new_data["user_id"] = user_id
        return await self.repository.update_post(post_id, user_id, new_data)

    async def delete_post(self, post_id: UUID, user_id: UUID):
        return await self.repository.delete_post(post_id, user_id)
