from pydantic_settings import BaseSettings
from typing import List, Optional
import secrets

class Settings(BaseSettings):
    # Database (Railway PostgreSQL — usa DATABASE_URL automáticamente)
    DATABASE_URL: str

    # JWT
    JWT_SECRET: str = secrets.token_urlsafe(32)
    JWT_EXPIRE: int = 1440          # 24 horas en minutos
    JWT_ALGORITHM: str = "HS256"

    # CORS — Vercel frontend
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # Entorno
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Redis (opcional en Railway)
    REDIS_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
