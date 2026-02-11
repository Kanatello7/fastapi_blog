from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRES_IN_MINUTES: int
    REFRESH_TOKEN_EXPIRES_IN_DAYS: int


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
