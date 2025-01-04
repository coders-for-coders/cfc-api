import os
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
import httpx

import jwt

from utils.data.mongo import MongoManager
from models.user import User, Session


class DiscordAuthRouter:
    def __init__(self):
        """Initialize the Discord authentication router with required config"""
        
        self.router = APIRouter(prefix="/api/auth")
        self.client_id = os.getenv("DISCORD_CLIENT_ID")
        self.client_secret = os.getenv("DISCORD_CLIENT_SECRET")
        self.callback_url = os.getenv("DISCORD_CALLBACK_URL")
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")
        self.db = MongoManager("auth_db")
        
        # Configure httpx client with timeouts and limits
        self.client_config = {
            "timeout": 10.0,
            "limits": httpx.Limits(max_keepalive_connections=5, max_connections=10)
        }
        
        # Initialize MongoDB connection
        self.db = MongoManager("auth_db")
        
        self._setup_routes()

    def _setup_routes(self):
        """Configure API routes"""
        self.router.add_api_route(path="/discord/login", endpoint=self.discord_login, methods=["GET"])
        self.router.add_api_route(path="/discord/callback", endpoint=self.discord_callback, methods=["GET"])
        self.router.add_api_route(path="/me", endpoint=self.get_current_user, methods=["GET"], response_model=User)

    def _generate_jwt(self, user_id: UUID) -> str:
        """Generate JWT token for user session"""
        return jwt.encode(
            {
                "sub": str(user_id),
                "exp": datetime.utcnow() + timedelta(days=1),
                "iat": datetime.utcnow(),
            },
            self.jwt_secret,
            algorithm="HS256"
        )

    async def discord_login(self) -> RedirectResponse:
        """Redirect user to Discord OAuth login page"""
        discord_auth_url = (
            f"https://discord.com/oauth2/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.callback_url}"
            f"&response_type=code"
            f"&scope=identify email"
        )
        return RedirectResponse(url=discord_auth_url)

    async def discord_callback(self, code: str, response: Response) -> dict:
        """Handle OAuth callback from Discord"""
        token_url = "https://discord.com/api/oauth2/token"
        
        async with httpx.AsyncClient(**self.client_config) as client:
            try:
                # Exchange code for access token
                token_response = await client.post(
                    token_url,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": self.callback_url,
                    }
                )
                token_response.raise_for_status()
                token_data = token_response.json()

                access_token = token_data.get("access_token")
                if not access_token:
                    raise HTTPException(status_code=400, detail="Failed to get access token")

                # Get user profile
                user_response = await client.get(
                    "https://discord.com/api/users/@me",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json"
                    }
                )
                user_response.raise_for_status()
                user_data = user_response.json()

                # Create/update user in database
                user = await self._upsert_user({
                    "discord_id": user_data["id"],
                    "username": user_data["username"],
                    "email": user_data.get("email"),
                    "avatar": user_data.get("avatar")
                })
                
                # Create session record
                session = await self._create_session(user.id, access_token)
                
                # Generate JWT
                token = self._generate_jwt(user.id)
                response.set_cookie(
                    key="session",
                    value=token,
                    httponly=True,
                    secure=True,
                    samesite="lax",
                    max_age=86400  # 24 hours
                )

                return {
                    "status": "success",
                    "user": {
                        "id": str(user.id),
                        "username": user.username,
                        "email": user.email,
                        "avatar": user.avatar
                    }
                }

            except httpx.HTTPError as e:
                raise HTTPException(status_code=400, detail=str(e))

    async def get_current_user(self, request: Request) -> User:
        """Get current authenticated user"""
        token = request.cookies.get("session")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            user_id = UUID(payload["sub"])
            session = await self._get_session(user_id)
            user = await self._get_user(user_id)
            return user
        except (jwt.InvalidTokenError, KeyError):
            raise HTTPException(status_code=401, detail="Invalid session token")

    async def _upsert_user(self, user_data: dict) -> User:
        """Create or update user record in database"""
        now = datetime.utcnow()
        
        # Try to find existing user by discord_id
        existing_user = await self.db.get_collection("users").find_one(
            {"discord_id": user_data["discord_id"]}
        )
        
        if existing_user:
            # Update existing user
            user_id = UUID(str(existing_user["_id"]))
            update_data = {
                "username": user_data["username"],
                "email": user_data["email"],
                "avatar": user_data["avatar"],
                "updated_at": now
            }
            updated_user = await self.db.update_document("users", str(user_id), update_data)
            return User(**updated_user)
        else:
            # Create new user
            new_user_data = {
                "id": str(uuid4()),
                "discord_id": user_data["discord_id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "avatar": user_data["avatar"],
                "created_at": now,
                "updated_at": now
            }
            created_user = await self.db.create_document("users", new_user_data)
            return User(**created_user)

    async def _create_session(self, user_id: UUID, access_token: str) -> Session:
        """Create new session record in database"""
        now = datetime.utcnow()
        session_data = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "access_token": access_token,
            "expires_at": now + timedelta(days=1)
        }
        created_session = await self.db.create_document("sessions", session_data)
        return Session(**created_session)

    async def _get_session(self, user_id: UUID) -> Session:
        """Retrieve active session for user"""
        session = await self.db.get_collection("sessions").find_one({
            "user_id": str(user_id),
            "expires_at": {"$gt": datetime.utcnow()}
        })
        if not session:
            raise HTTPException(status_code=401, detail="No active session found")
        session["id"] = str(session.pop("_id"))
        return Session(**session)

    async def _get_user(self, user_id: UUID) -> User:
        """Retrieve user by ID"""
        user = await self.db.get_document_by_id("users", str(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return User(**user)