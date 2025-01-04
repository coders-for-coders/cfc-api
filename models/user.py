from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class User(BaseModel):
    id: UUID
    username: str
    email: Optional[str]
    avatar: Optional[str]
    created_at: datetime
    updated_at: datetime
    discord_id: Optional[str] = None
    github_id: Optional[int] = None

class Session(BaseModel):
    id: UUID
    user_id: UUID
    access_token: str
    expires_at: datetime