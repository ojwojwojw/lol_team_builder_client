from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_allowed_origins
from .controllers.auth_controller import router as auth_router
from .controllers.firestore_admin_controller import router as firestore_admin_router
from .controllers.match_controller import router as match_router
from .controllers.riot_controller import router as riot_router


def create_app() -> FastAPI:
    app = FastAPI()

    allowed_origins = get_allowed_origins()
    if allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(auth_router)
    app.include_router(firestore_admin_router)
    app.include_router(riot_router)
    app.include_router(match_router)

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
