from fastapi import status

from src.exceptions import BaseAPIException


class InvalidTokenException(BaseAPIException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

class TokenExpiredException(BaseAPIException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")


class InvalidCredentialsException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
class UserExistsException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists",
        )
