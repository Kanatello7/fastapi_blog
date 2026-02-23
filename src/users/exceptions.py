from fastapi import status

from src.exceptions import BaseAPIException


class UserNotFoundException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exists"
        )


class FollowYourselfException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="You can't follow yourself",
        )


class AlreadyFollowingException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT, detail="You already follow this user"
        )


class NotFollowingException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You can't unfollow the user you do not follow",
        )
