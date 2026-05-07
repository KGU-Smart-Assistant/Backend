from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.seed import seed_contacts_from_json, seed_places_from_json
from app.db.session import SessionLocal


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
    )
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.on_event("startup")
    def _seed_db() -> None:
        with SessionLocal() as db:
            seed_places_from_json(db)
            seed_contacts_from_json(db)

    return app


app = create_app()
