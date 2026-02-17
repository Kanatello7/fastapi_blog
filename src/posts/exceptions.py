from fastapi import status

from src.exceptions import BaseAPIException


class PostNotFoundException(BaseAPIException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


class PostAccessDeniedException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don't have access to this post",
        )


class CommentNotFoundException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )


class CommentAccessDeniedException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you don't have access to this comment",
        )


class TagNotFoundException(BaseAPIException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
