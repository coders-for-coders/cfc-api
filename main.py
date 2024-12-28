from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import uvicorn

from core.app import app
from core.logger import logger
from routes.auth import GithubAuth
from routes.data import DataRouter

data_router = DataRouter()
auth_router = GithubAuth()

docs_router = APIRouter(prefix="/api")
docs_router.add_api_route(
    path="/docs",
    endpoint=lambda: HTMLResponse(content=open("./docs/docs.html").read()),
    methods=["GET"]
)

health_router = APIRouter(prefix="/api")
health_router.add_api_route(
    path="/health",
    endpoint=app.health_check,
    methods=["GET"]
)

app.configure_routes([
    data_router.router,
    auth_router.router,
    docs_router,
    health_router
])

if __name__ == "__main__":
    try:
        uvicorn.run(
            app.get_application(),
            host="0.0.0.0",
            port=8000,
            log_config=None
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise
    finally:
        app.cleanup()
