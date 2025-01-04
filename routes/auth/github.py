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


class GithubAuthRouter:
    def __init__(self):
        """Initialize the GitHub authentication router with required config"""

        self.router = APIRouter(prefix="/api/auth")
        self.client_id = os.getenv("GH_CLIENT_ID")
        self.client_secret = os.getenv("GH_CLIENT_SECRET") 
        self.callback_url = os.getenv("GH_CALLBACK_URL")
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")
        self.org_name = "coders-for-coders"
        
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
        self.router.add_api_route(path="/github/login", endpoint=self.github_login, methods=["GET"])
        self.router.add_api_route(path="/github/callback", endpoint=self.github_callback, methods=["GET"])
        self.router.add_api_route(path="/github/org/join", endpoint=self.join_org, methods=["POST"])
        self.router.add_api_route(path="/me", endpoint=self.get_current_user, methods=["GET"], response_model=User)

    async def github_login(self) -> RedirectResponse:
        
        state = self._generate_state_token()
        github_auth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.callback_url}"
            f"&state={state}"
            f"&scope=read:user,user:email,read:org"
        )
        response = RedirectResponse(url=github_auth_url)
        response.set_cookie(
            key="oauth_state",
            value=state,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=300  # 5 minutes
        )
        return response

    def _generate_state_token(self) -> str:
        
        return jwt.encode(
            {
                "exp": datetime.utcnow() + timedelta(minutes=5),
                "iat": datetime.utcnow(),
            },
            self.jwt_secret,
            algorithm="HS256"
        )

    async def github_callback(self, code: str, state: str, request: Request, response: Response) -> dict:
       
        # stored_state = request.cookies.get("oauth_state")
        # if not stored_state or stored_state != state:
        #     raise HTTPException(status_code=400, detail="Invalid state parameter")
            
        token_url = "https://github.com/login/oauth/access_token"
        
        async with httpx.AsyncClient(**self.client_config) as client:
            try:
                token_response = await client.post(
                    token_url,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                    },
                    headers={"Accept": "application/json"}
                )
                token_response.raise_for_status()
                token_data = token_response.json()

                access_token = token_data.get("access_token")
                if not access_token:
                    raise HTTPException(status_code=400, detail="Failed to get access token")

                user_response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json"
                    }
                )
                user_response.raise_for_status()
                user_data = user_response.json()

                email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json"
                    }
                )
                email_response.raise_for_status()
                primary_email = next(
                    (email for email in email_response.json() if email["primary"]),
                    None
                )

                user = await self._upsert_user({
                    "github_id": user_data["id"],
                    "username": user_data["login"],
                    "email": primary_email["email"] if primary_email else None,
                    "avatar": user_data.get("avatar_url")
                })
                
                session = await self._create_session(user.id, access_token)
                
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
                print(e)
                raise HTTPException(status_code=400, detail=str(e))

    async def get_current_user(self, request: Request) -> User:
        """Get the current authenticated user"""
        token = request.cookies.get("session")
        if not token:
            raise HTTPException(status_code=401, detail="No session token provided")
            
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            user_id = UUID(payload["sub"])
            user = await self.db.get_document("users", str(user_id))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return User(**user)
        except (jwt.InvalidTokenError, KeyError):
            raise HTTPException(status_code=401, detail="Invalid session token")

    async def join_org(self, request: Request) -> dict:

        token = request.cookies.get("session")
        if not token:
            raise HTTPException(status_code=401, detail="No session token provided")
            
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            user_id = payload["sub"]
            session = await self._get_session(user_id)
            access_token = session.access_token
        except (jwt.InvalidTokenError, KeyError):
            raise HTTPException(status_code=401, detail="Invalid session token")

        async with httpx.AsyncClient(**self.client_config) as client:
            try:
                user_response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json"
                    }
                )
                user_response.raise_for_status()
                user_data = user_response.json()

                invite_response = await client.post(
                    f"https://api.github.com/orgs/{self.org_name}/invitations",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28"
                    },
                    json={
                        "invitee_id": user_data["id"],
                        "role": "direct_member"
                    }
                )
                invite_response.raise_for_status()

                return {"message": f"Invitation sent to join {self.org_name}"}

            except httpx.HTTPError as e:
                raise HTTPException(status_code=400, detail=str(e))

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

    async def _upsert_user(self, user_data: dict) -> User:
        """Create or update user record in database"""
        now = datetime.utcnow()
        
        existing_user = await self.db.get_collection("users").find_one(
            {"github_id": user_data["github_id"]}
        )
        
        if existing_user:
            user_id = existing_user["_id"]
            update_data = {
                "username": user_data["username"],
                "email": user_data["email"],
                "avatar": user_data.get("avatar"),
                "updated_at": now
            }
            updated_user = await self.db.update_document("users", str(user_id), update_data)
            return User(**updated_user)
        else:
            # Create new user
            new_user_data = {
                "github_id": user_data["github_id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "avatar": user_data.get("avatar"),
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