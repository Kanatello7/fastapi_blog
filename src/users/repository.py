from uuid import UUID

from sqlalchemy import exists, func, select

from src.core.utils import CRUDRepository
from src.users.models import Follower, User


class FollowerRepository(CRUDRepository):
    model = Follower

    async def get_user_followers(self, user_id: UUID, curr_user_id: UUID):
        is_followed_by_me = (
            exists()
            .where(
                Follower.follower_id == curr_user_id,
                Follower.following_id == User.id,
            )
            .correlate(User)
        )
        query = (
            select(User, is_followed_by_me.label("is_followed_by_me"))
            .join(Follower, User.id == Follower.follower_id)
            .where(Follower.following_id == user_id)
        )
        results = await self.session.execute(query)
        users = []
        for row in results.all():
            user = row.User
            user.is_followed_by_me = row.is_followed_by_me
            users.append(user)
        return users

    async def get_user_following(self, user_id: UUID, curr_user_id: UUID):
        is_followed_by_me = (
            exists()
            .where(
                Follower.follower_id == curr_user_id,
                Follower.following_id == User.id,
            )
            .correlate(User)
        )

        query = (
            select(User, is_followed_by_me.label("is_followed_by_me"))
            .join(Follower, User.id == Follower.following_id)
            .where(Follower.follower_id == user_id)
        )

        results = await self.session.execute(query)
        users = []
        for row in results.all():
            user = row.User
            user.is_followed_by_me = row.is_followed_by_me
            users.append(user)

        return users

    async def is_user_following(self, user_id: UUID, curr_user_id: UUID):
        user_follows = exists().where(
            Follower.following_id == user_id, Follower.follower_id == curr_user_id
        )
        query = select(user_follows.label("is_following"))
        result = await self.session.execute(query)
        return result.one()

    async def get_user_stats(self, user_id: UUID, curr_user_id: UUID):
        followers_count = (
            select(func.count())
            .where(Follower.following_id == user_id)
            .scalar_subquery()
        )
        following_count = (
            select(func.count())
            .where(Follower.follower_id == user_id)
            .scalar_subquery()
        )
        is_followed = exists().where(
            Follower.follower_id == curr_user_id,
            Follower.following_id == user_id,
        )

        query = select(
            followers_count.label("followers_count"),
            following_count.label("following_count"),
            is_followed.label("is_followed"),
        )

        result = await self.session.execute(query)
        row = result.one()

        return {
            "followers_count": row.followers_count,
            "following_count": row.following_count,
            "is_followed": row.is_followed,
        }


class UserRepository(CRUDRepository):
    model = User
