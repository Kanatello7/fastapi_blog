from fastapi import status

from src.exceptions import BaseAPIException


class UserNotFoundException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exists"
        )
