from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import engine

settings = get_settings()


def create_app() -> FastAPI:

    app = FastAPI(
        title=settings.APP_NAME,
        description="Асинхронный сервис процессинга платежей",
        version="1.0.0",
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):

        async with engine.begin() as conn:
            from app.models.outbox import Outbox
            from app.models.payment import Payment

            await conn.run_sync(Payment.metadata.create_all)
            await conn.run_sync(Outbox.metadata.create_all)
        yield

    app.router.lifespan_context = lifespan

    @app.get("/")
    async def root():
        return {
            "service": settings.APP_NAME,
            "status": "healthy",
            "docs": "/docs",
        }

    @app.get("/health")
    async def health_check():

        return {"status": "ok"}

    from api.v1 import endpoints

    app.include_router(endpoints.router, prefix="/api/v1", tags=["Payments"])

    return app


app = create_app()
