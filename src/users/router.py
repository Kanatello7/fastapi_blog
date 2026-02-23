from uuid import UUID

from fastapi import APIRouter, status

from src.auth.dependencies import GetCurrentUserDep
from src.users.dependencies import FollowerServiceDep
from src.users.schemas import FollowResponse, UserResponse, UserStatsResponse

router = APIRouter()


@router.post(
    "/{user_id}/follow",
    status_code=status.HTTP_201_CREATED,
    response_model=FollowResponse,
)
async def follow_user(
    user_id: UUID, curr_user: GetCurrentUserDep, service: FollowerServiceDep
):
    return await service.follow_user(user_id=user_id, curr_user_id=curr_user.id)


@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    user_id: UUID, curr_user: GetCurrentUserDep, service: FollowerServiceDep
):
    await service.unfollow_user(user_id=user_id, curr_user_id=curr_user.id)


@router.get(
    "/{user_id}/followers",
    status_code=status.HTTP_200_OK,
    response_model=list[UserResponse],
)
async def get_user_followers(user_id: UUID, service: FollowerServiceDep):
    pass


@router.get(
    "/{user_id}/following",
    status_code=status.HTTP_200_OK,
    response_model=list[UserResponse],
)
async def get_user_following(user_id: UUID, service: FollowerServiceDep):
    pass


@router.get("/{user_id}/follow", status_code=status.HTTP_200_OK)
async def is_user_following(
    user_id: UUID, curr_user: GetCurrentUserDep, service: FollowerServiceDep
):
    pass


@router.get(
    "/{user_id}/stats", status_code=status.HTTP_200_OK, response_model=UserStatsResponse
)
async def get_user_stats(user_id: UUID, service: FollowerServiceDep):
    pass
