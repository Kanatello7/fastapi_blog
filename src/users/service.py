from uuid import UUID

from src.core.exceptions import ForeignKeyConstraintError, UniqueConstraintError
from src.users.exceptions import (
    AlreadyFollowingException,
    FollowYourselfException,
    NotFollowingException,
    UserNotFoundException,
)
from src.users.repository import FollowerRepository, UserRepository


class FollowerService:
    def __init__(self, repo: FollowerRepository):
        self.repository = repo

    async def follow_user(self, user_id: UUID, curr_user_id: UUID):
        if user_id == curr_user_id:
            raise FollowYourselfException
        data = {"follower_id": curr_user_id, "following_id": user_id}
        try:
            return await self.repository.create(new_data=data)
        except UniqueConstraintError as e:
            raise AlreadyFollowingException() from e
        except ForeignKeyConstraintError as e:
            raise UserNotFoundException() from e

    async def unfollow_user(self, user_id: UUID, curr_user_id: UUID):
        result = await self.repository.delete_one_or_more(
            following_id=user_id, follower_id=curr_user_id
        )
        if not result:
            raise NotFollowingException()
        return result[0]

    async def get_user_followers(self, user_id: UUID, curr_user_id: UUID):
        return await self.repository.get_user_followers(
            user_id=user_id, curr_user_id=curr_user_id
        )

    async def get_user_following(self, user_id: UUID, curr_user_id: UUID):
        return await self.repository.get_user_following(
            user_id=user_id, curr_user_id=curr_user_id
        )

    async def is_user_following(self, user_id: UUID, curr_user_id: UUID):
        return await self.repository.is_user_following(
            user_id=user_id, curr_user_id=curr_user_id
        )

    async def get_user_stats(self, user_id: UUID, curr_user_id: UUID):
        result = await self.repository.get_user_stats(
            user_id=user_id, curr_user_id=curr_user_id
        )
        return result


class UserService:
    def __init__(self, repo: UserRepository):
        self.repository = repo

    async def get_user(self, user_id: UUID):
        result = await self.repository.get_one_or_many(id=user_id)
        return result[0] if result else None
