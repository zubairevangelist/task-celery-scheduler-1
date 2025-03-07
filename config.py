from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str = "default_user"
    POSTGRES_PASSWORD: str = "default_password"
    POSTGRES_DB: str = "default_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    DEBUG: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
