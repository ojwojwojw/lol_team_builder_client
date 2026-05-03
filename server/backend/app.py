from fastapi import FastAPI

from .controllers.auth_controller import router as auth_router
from .controllers.match_controller import router as match_router
from .controllers.riot_controller import router
from .database import init_db


def create_app() -> FastAPI:
    # FastAPI 앱 조립은 여기서만 담당한다.
    # 새 컨트롤러를 추가할 때는 router include를 이 함수에 모으면 된다.
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(router)
    app.include_router(match_router)

    @app.on_event("startup")
    def on_startup() -> None:
        # 서버가 뜰 때 필요한 최소한의 DB 준비를 보장한다.
        init_db()

    return app


app = create_app()
