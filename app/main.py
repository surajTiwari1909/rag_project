from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.core.config import get_settings
from app.db.session import check_database_connection

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    check_database_connection()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(
    health_router,
    prefix=settings.api_v1_prefix,
)
# if we have more app the we can add more route for now we 
# have only one route health check so we add this 


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
    }
