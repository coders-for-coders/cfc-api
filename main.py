import dotenv

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
import uvicorn


from core.app import App
from core.logger import Logger
from routes.auth.discord import DiscordAuthRouter
from routes.auth.github import GithubAuthRouter
from routes.data.data import DataRouter

dotenv.load_dotenv()

class APIServer:
    def __init__(self):
        self.app = App()
        self.logger = Logger()
        self._setup_routers()

    def _setup_routers(self):
     
        self.data_router = DataRouter()
        self.github_router = GithubAuthRouter()
        self.discord_router = DiscordAuthRouter()
        
        self.app.configure_routes([
            self.data_router.router,
            self.github_router.router,
            self.discord_router.router,
            self._docs_router(),
            self._health_router()
        ])

    def _docs_router(self) -> APIRouter:
        """Create and configure documentation router"""
        docs_router = APIRouter(prefix="/api")
        docs_router.add_api_route(
            path="/docs",
            endpoint=lambda: HTMLResponse(content=open("./docs/docs.html").read()),
            methods=["GET"]
        )
        return docs_router

    def _health_router(self) -> APIRouter:
        """Create and configure health check router"""
        health_router = APIRouter(prefix="/api")
        health_router.add_api_route(
            path="/health",
            endpoint=self.app.health_check,
            methods=["GET"]
        )
        return health_router

    def run(self):
        try:
            uvicorn.run(
                self.app.get_application(),
                host="0.0.0.0",
                port=8000,
                log_config=None
            )
        except Exception as e:
            self.logger.error(f"Failed to start server: {str(e)}")
            raise
        finally:
            self.app.cleanup()


if __name__ == "__main__":
    server = APIServer()
    server.run()
