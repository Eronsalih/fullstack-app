from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import create_client, get_db
from .routers import tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = create_client()
    app.state.db = client[settings.mongo_db]
    yield
    client.close()


app = FastAPI(
    title="Fullstack App API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api")


@app.get("/api/health", tags=["health"])
async def health(db=Depends(get_db)):
    try:
        await db.command("ping")
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok", "database": "up"}
