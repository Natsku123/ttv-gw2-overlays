import os
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    ROOT_PATH: str | None = os.environ.get("ROOT_PATH")

    ORIGINS: list[AnyHttpUrl] = [
        os.environ.get("HOSTNAME", "http://localhost:8800"),
    ]

    VERSION: str = os.environ.get("VERSION", "UNKNOWN")
    BUILD: str = os.environ.get("BUILD", "UNKNOWN")

    class Config:
        case_sensitive = True


settings = Settings()
