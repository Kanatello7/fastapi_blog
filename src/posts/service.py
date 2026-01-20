from uuid import UUID

from src.posts.models import Post
from src.posts.repository import PostRepository


class PostService:
    def __init__(self, repo: PostRepository):
        self.repository = repo 

    async def get_post(self, *args, **kwargs) -> Post:
        return await self.repository.get_post(*args, **kwargs)

    async def get_user_posts(self, user_id: UUID):
        return await self.repository.get_user_posts(user_id)