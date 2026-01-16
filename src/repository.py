from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Post


class PostRepository():
    def __init__(self, session: AsyncSession):
        self.session = session 

    async def get_posts(self) -> list[Post]:
        query = text("SELECT * FROM posts ORDER BY date_posted DESC;")
        results = await self.session.execute(query)
        return results.scalars().all()
    
    async def get_post(self, post_id: UUID) -> Post:
        query = text(f"SELECT * FROM posts WHERE id={post_id};")
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_post(self, new_post: dict) -> Post:
        stmt = text(f"INSERT INTO posts(author, title, content) VALUES({new_post["author"]}, {new_post["title"], {new_post["content"]}}) RETURNING *;")
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
    
    async def update_post(self, post_id: UUID, updated_post: dict) -> Post:
        stmt = text(f"UPDATE posts SET author={updated_post["author"]}, title={updated_post["title"]}, content={updated_post["content"]} WHERE id={post_id};")
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalar_one()
    
    async def delete_post(self, post_id: UUID):
        stmt = text(f"DELETE posts WHERE id={post_id};")
        await self.session.execute(stmt)
        await self.session.commit()

    

    