from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    admin,
    analytics,
    auth,
    products,
    reports,
    scans,
    violations,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="LabelGuard AI",
        description=(
            "AI compliance checking for packaged commodities under Legal "
            "Metrology (Packaged Commodities) Rules, 2011"
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/v1")
    app.include_router(scans.router, prefix="/v1")
    app.include_router(products.router, prefix="/v1")
    app.include_router(reports.router, prefix="/v1")
    app.include_router(analytics.router, prefix="/v1")
    app.include_router(admin.router, prefix="/v1")
    app.include_router(violations.router, prefix="/v1")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
