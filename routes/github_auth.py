import os

from fastapi import APIRouter, HTTPException, Request
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
                "https://api.github.com/user/repos",
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
        
class DiscordAuthRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/auth")
        
        self.client_id = os.getenv("DISCORD_CLIENT_ID")
        self.client_secret = os.getenv("DISCORD_CLIENT_SECRET")
        self.redirect_uri = "http://localhost:1500/api/auth/discord/redirect"
        self.discord_api_base_url = "https://discord.com/api"
        self.oauth2_url = "https://discord.com/oauth2/authorize"
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route(path="/discord/login", endpoint=self.discord_login, methods=["GET"])
        self.router.add_api_route(path="/discord/redirect", endpoint=self.discord_callback, methods=["GET"])

    async def discord_login(self):
        auth_url = (
            f"{self.oauth2_url}"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope=email identify"
        )
        return RedirectResponse(auth_url)

    async def discord_callback(self, request: Request):
        code = request.query_params.get("code")
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not found")

        token_url = f"{self.discord_api_base_url}/oauth2/token"
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data, headers=headers)
            token_json = token_response.json()

            if "access_token" not in token_json:
                raise HTTPException(status_code=400, detail=token_json.get("error_description", "Failed to fetch token"))

            access_token = token_json["access_token"]

            user_url = f"{self.discord_api_base_url}/users/@me"
            headers = {"Authorization": f"Bearer {access_token}"}

            user_response = await client.get(user_url, headers=headers)
            user_info = user_response.json()

            user_id = user_info["id"]
            username = user_info["username"]
            discriminator = user_info.get("discriminator", "0")
            email = user_info.get("email")
            avatar_hash = user_info.get("avatar")
            avatar_url = (
                f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png" if avatar_hash else None
            )


            return


            #TODO 1. Create/update user in your database
            #TODO 2. Create a session
            #TODO 3. Return a JWT token or set a cookie
