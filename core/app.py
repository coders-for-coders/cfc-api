import time

from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from core.logger import logger
from utils.data.mongo import MongoManager

class App:
    def __init__(self):
        self.app = FastAPI(
            title="Coders For Coders API",
            docs_url=None,
            redoc_url=None,
            openapi_url=None
        )
        self.db = MongoManager()
        self._configure_cors()
        self.logger = logger
        self.app.middleware("http")(self.log_requests)
        self.app.get("/api/docs")(self.get_docs)
        self.app.get("/openapi.json")(self.get_openapi_schema)
        
    def _configure_cors(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    async def get_openapi_schema(self):
        openapi_schema = get_openapi(
            title="Coders For Coders API",
            version="0.0.1",
            description="API for the Coders For Coders project",
            routes=self.app.routes
        )
        return openapi_schema

    async def get_docs(self):
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="API Documentation",
            swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
        )

    async def log_requests(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        self.logger.info(
            f"request: {request.method} - {request.url.path} "
            f"status: {response.status_code} "
            f"duration: {duration:.2f}s"
        )
        return response

    def configure_routes(self, routers: list[APIRouter]):
        for router in routers:
            self.app.include_router(router)
            if not router.prefix == '/api':
                self.logger.info(f"Registered router: {router.prefix}")
    
    def get_application(self) -> FastAPI:
        return self.app

    @property
    def db_client(self):
        return self.db.client

    async def health_check(self):
        try:
            server_info = await self.db.client.server_info()
            return {
                "status": "healthy",
                "database": {
                    "status": "connected",
                    "version": server_info.get("version", "unknown"),
                    "connections": server_info.get("connections", {}).get("current", 0)
                },
                "api_version": self.app.version,
                "api_title": self.app.title
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy", 
                "database": {
                    "status": "disconnected",
                    "error": str(e)
                },
                "api_version": self.app.version,
                "api_title": self.app.title
            }

    def cleanup(self):
        self.logger.info("Cleaning up resources...")
        self.db.close()

app = App()
