from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import settings


def create_client() -> AsyncIOMotorClient:
    """Motor connects lazily, so the app can start before MongoDB is ready."""
    auth = {}
    if settings.mongo_user:
        auth = {
            "username": settings.mongo_user,
            "password": settings.mongo_password,
            "authSource": "admin",
        }
    return AsyncIOMotorClient(
        host=settings.mongo_host,
        port=settings.mongo_port,
        serverSelectionTimeoutMS=3000,
        **auth,
    )


def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.db
