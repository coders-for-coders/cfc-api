import os

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import httpx

class DiscordAuthRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/auth")
        self.client_id = os.getenv("DISCORD_CLIENT_ID")
        self.client_secret = os.getenv("DISCORD_CLIENT_SECRET")
        self.callback_url = os.getenv("DISCORD_CALLBACK_URL")
        self._setup_routes()


    def _setup_routes(self):
        self.router.add_api_route(path="/discord/login", endpoint=self.discord_login, methods=["GET"])
        self.router.add_api_route(path="/discord/callback", endpoint=self.discord_callback, methods=["GET"])

    async def discord_login(self):
        discord_auth_url = f"https://discord.com/oauth2/authorize?client_id={self.client_id}&redirect_uri={self.callback_url}&response_type=code&scope=identify"
        return RedirectResponse(url=discord_auth_url)

    async def discord_callback(self, code: str):
        token_url = "https://discord.com/api/oauth2/token"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": self.callback_url,
                },
            )

        return response.json()