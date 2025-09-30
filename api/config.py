from pydantic_settings import BaseSettings
from functools import lru_cache


class Config(BaseSettings):

    API_KEYS: str

    REDIS_URL: str = "redis://localhost"
    CACHE_OSM_EXPIRY: int = 3600 * 24  # 24 hours
    # Geneva and Leman areas by default
    CACHE_OSM_AREAS: str = "[[5.829620,46.055305,6.420135,46.425730],[6.252594,46.293045,7.027130,46.620381]]"

    OTP_URL: str = "https://lasur-otp.epfl.ch"


@lru_cache()
def get_config():
    return Config()


config = get_config()
