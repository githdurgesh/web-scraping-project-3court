# from dataclasses import dataclass


# @dataclass(frozen=True)
# class Settings:
#     timeout: int = 60
#     user_agent: str = "Mozilla/5.0"


# settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    timeout: int = 60
    user_agent: str = "Mozilla/5.0"
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()

