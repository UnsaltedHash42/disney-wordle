"""Application configuration using Pydantic BaseSettings."""

from functools import lru_cache
from typing import Optional
from datetime import timedelta

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Flask Configuration
    flask_env: str = Field(default="development", env="FLASK_ENV")
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    debug: bool = Field(default=True, env="DEBUG")
    testing: bool = Field(default=False, env="TESTING")
    
    # JWT Configuration  
    jwt_secret_key: str = Field(default="jwt-dev-secret-key-change-in-production", env="JWT_SECRET_KEY")
    jwt_access_token_expires: int = Field(default=900, env="JWT_ACCESS_TOKEN_EXPIRES")  # 15 minutes
    jwt_refresh_token_expires: int = Field(default=2592000, env="JWT_REFRESH_TOKEN_EXPIRES")  # 30 days
    
    # Database Configuration
    database_url: str = Field(default="postgresql://username:password@localhost:5432/wordle_db", env="DATABASE_URL")
    pool_size: int = Field(default=10, env="POOL_SIZE")
    max_overflow: int = Field(default=20, env="MAX_OVERFLOW")
    pool_pre_ping: bool = Field(default=True, env="POOL_PRE_PING")
    
    # Rate Limiting
    rate_limit_storage_url: str = Field(default="memory://", env="RATE_LIMIT_STORAGE_URL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Email Configuration (for future use)
    mail_server: Optional[str] = Field(default=None, env="MAIL_SERVER")
    mail_port: int = Field(default=587, env="MAIL_PORT")
    mail_use_tls: bool = Field(default=True, env="MAIL_USE_TLS")
    mail_username: Optional[str] = Field(default=None, env="MAIL_USERNAME")
    mail_password: Optional[str] = Field(default=None, env="MAIL_PASSWORD")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_flask_config() -> dict:
    """Convert Pydantic settings to Flask config dict."""
    settings = get_settings()
    
    return {
        "SECRET_KEY": settings.secret_key,
        "DEBUG": settings.debug,
        "TESTING": settings.testing,
        "SQLALCHEMY_DATABASE_URI": settings.database_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "pool_size": settings.pool_size,
            "max_overflow": settings.max_overflow,
            "pool_pre_ping": settings.pool_pre_ping,
        },
        "JWT_SECRET_KEY": settings.jwt_secret_key,
        "JWT_ACCESS_TOKEN_EXPIRES": timedelta(seconds=settings.jwt_access_token_expires),
        "JWT_REFRESH_TOKEN_EXPIRES": timedelta(seconds=settings.jwt_refresh_token_expires),
        "RATELIMIT_STORAGE_URL": settings.rate_limit_storage_url,
    } 