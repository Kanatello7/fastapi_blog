from uuid import UUID

from fastapi import APIRouter, status

from src.auth.dependencies import GetCurrentUserDep
from src.users.dependencies import FollowerServiceDep, UserServiceDep, ValidUserDep
from src.users.schemas import (
    FollowerResponse,
    FollowResponse,
    IsFollowingResponse,
    UserStatsResponse,
)

router = APIRouter()


@router.post(
    "/{user_id}/follow",
    status_code=status.HTTP_201_CREATED,
    response_model=FollowResponse,
)
async def follow_user(
    user: ValidUserDep, curr_user: GetCurrentUserDep, service: FollowerServiceDep
):
    return await service.follow_user(user_id=user.id, curr_user_id=curr_user.id)


@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    user: ValidUserDep, curr_user: GetCurrentUserDep, service: FollowerServiceDep
):
    await service.unfollow_user(user_id=user.id, curr_user_id=curr_user.id)


@router.get(
    "/{user_id}/followers",
    status_code=status.HTTP_200_OK,
    response_model=list[FollowerResponse],
)
async def get_user_followers(
    user: ValidUserDep,
    curr_user: GetCurrentUserDep,
    service: FollowerServiceDep,
):
    return await service.get_user_followers(user_id=user.id, curr_user_id=curr_user.id)


@router.get(
    "/{user_id}/following",
    status_code=status.HTTP_200_OK,
    response_model=list[FollowerResponse],
)
async def get_user_following(
    user: ValidUserDep,
    curr_user: GetCurrentUserDep,
    service: FollowerServiceDep,
):
    return await service.get_user_following(user_id=user.id, curr_user_id=curr_user.id)


@router.get(
    "/{user_id}/follow",
    status_code=status.HTTP_200_OK,
    response_model=IsFollowingResponse,
)
async def is_user_following(
    user: ValidUserDep,
    curr_user: GetCurrentUserDep,
    service: FollowerServiceDep,
):
    return await service.is_user_following(user_id=user.id, curr_user_id=curr_user.id)


@router.get(
    "/{user_id}/stats", status_code=status.HTTP_200_OK, response_model=UserStatsResponse
)
async def get_user_stats(
    user: ValidUserDep,
    curr_user: GetCurrentUserDep,
    service: FollowerServiceDep,
):
    return await service.get_user_stats(user_id=user.id, curr_user_id=curr_user.id)
