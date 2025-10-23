"""Module to define the application settings"""

from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Module to define the application settings"""

    PROJECT_NAME: str = "AI Editor Agent"
    API_PREFIX: str = "/api"
    GCS_BUCKET_NAME: str = "creative-audit-scratch-pad"
    CDN_DOMAIN: str = "creative-audit.prd.cdn.polaris.prd.ext.wpromote.com"
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = [
        "http://localhost",
        "http://localhost:4200",
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str] | str:
        """Validate CORS"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)


settings = Settings()
