from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    API_KEYS: str

    REDIS_URL: str = "redis://localhost"
    CACHE_OSM_EXPIRY: int = 3600 * 24  # 24 hours
    # Geneva and Leman areas by default
    CACHE_OSM_AREAS: str = "[[5.829620,46.055305,6.420135,46.425730],[6.252594,46.293045,7.027130,46.620381]]"

    OTP_URL: str = "https://lasur-otp.epfl.ch"

    LFS_USERNAME: str = "" # only used on build
    LFS_PASSWORD: str = "" # only used on build
    LFS_SERVER_PATH: str = "" # only used on build


@lru_cache()
def get_config():
    return Config()


config = get_config()
