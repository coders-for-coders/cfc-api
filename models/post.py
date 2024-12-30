from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class PostMetadata(BaseModel):
    """Contains metadata about the post like creation date and type"""
    created_at: datetime = Field(default_factory=datetime.now, description="Creation date of the post")
    updated_at: Optional[datetime] = None
    type: str = Field(description="The type/category of the post")
    icon: Optional[str] = None
    author: str = Field(description="Username of the post author")
    tags: List[str] = Field(default_factory=list, description="Tags/topics for the post")

class Comment(BaseModel):
    """Represents a comment on a post"""
    id: str = Field(description="Unique identifier for the comment")
    author: str = Field(description="Username of the comment author")
    content: str = Field(description="Content of the comment")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation date of the comment")

class PostContent(BaseModel):
    """Contains the actual content and descriptions of the post"""
    title: str = Field(description="Title of the post")
    description: str = Field(description="Short description for preview")
    long_description: Optional[str] = Field(None, description="Detailed description of the post")
    content: str = Field(description="Main content of the post")
    images: Optional[List[str]] = Field(None, description="List of image URLs")
    likes: int = Field(default=0, description="Number of likes on the post")
    comments: List[Comment] = Field(default_factory=list, description="Comments on the post")

class Post(BaseModel):
    """Represents a complete post with metadata and content"""
    id: str = Field(description="Unique identifier for the post")
    metadata: PostMetadata = Field(description="Metadata about the post")
    content: PostContent = Field(description="Content of the post")
