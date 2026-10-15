import os


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    """All configuration comes from environment variables."""

    mongo_host: str = os.getenv("MONGO_HOST", "localhost")
    mongo_port: int = int(os.getenv("MONGO_PORT", "27017"))
    mongo_user: str = os.getenv("MONGO_USER", "")
    mongo_password: str = os.getenv("MONGO_PASSWORD", "")
    mongo_db: str = os.getenv("MONGO_DB", "appdb")
    cors_origins: list[str] = _split(
        os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    )


settings = Settings()
