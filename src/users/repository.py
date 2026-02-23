from uuid import UUID

from sqlalchemy import select

from src.core.utils import CRUDRepository
from src.users.models import Follower, User


class FollowerRepository(CRUDRepository):
    model = Follower

    async def get_user_followers(self, user_id: UUID):
        query = (
            select(User)
            .join(Follower, User.id == Follower.follower_id)
            .where(User.id == user_id)
        )
