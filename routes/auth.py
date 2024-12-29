import os

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import httpx

class GithubAuthRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/auth")
        
        self.client_id = os.getenv("GITHUB_CLIENT_ID")
        self.client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        self.callback_url = os.getenv("GITHUB_CALLBACK_URL")
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route(path="/github/login", endpoint=self.github_login, methods=["GET"])
        self.router.add_api_route(path="/github/callback", endpoint=self.github_callback, methods=["GET"])

    async def github_login(self):
        github_auth_url = f"https://github.com/login/oauth/authorize?client_id={self.client_id}&redirect_uri={self.callback_url}"
        return RedirectResponse(url=github_auth_url)

    async def github_callback(self, code: str):
        token_url = "https://github.com/login/oauth/access_token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                },
                headers={"Accept": "application/json"}
            )
            
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                return {"error": "Failed to get access token"}
        
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            user_data = user_response.json()
            
            #TODO 1. Create/update user in your database
            #TODO 2. Create a session
            #TODO 3. Return a JWT token or set a cookie
            
            return user_data