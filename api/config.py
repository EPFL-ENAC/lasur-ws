from pydantic_settings import BaseSettings
from functools import lru_cache


class Config(BaseSettings):

    API_KEYS: str

    REDIS_URL: str = "redis://localhost"
    CACHE_OSM_EXPIRY: int = 600

    OTP_URL: str = "https://lasur-otp.epfl.ch"


@lru_cache()
def get_config():
    return Config()


config = get_config()
