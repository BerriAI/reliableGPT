from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Validations and defaults for environment variables. In the future this should be used to load
    and validate all the env variables as it's currently the preferred go-to approach in Python world"""

    ENVIRONMENT: str = Field(env="ENVIRONMENT", default="local")
    APP_NAME: str = "reliablegpt"

    REDIS_HOST: str = Field(env="REDIS_HOST", default="localhost")
    REDIS_PORT: int = Field(env="REDIS_PORT", default=6379)
    REDIS_DB: int = Field(env="REDIS_DB", default=0)

    class Config:
        env_file = ".env"


settings = Settings()
