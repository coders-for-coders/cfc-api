import fastapi
import uvicorn
import os
from dotenv import load_dotenv
import motor
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel

load_dotenv()
db = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
database = db.resources_db

app = fastapi.FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResourceContent(BaseModel):
    id: int
    title: str
    content: str
    resourceType: str

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/api/resources")
async def get_resources():
    resources = [
        {
            "title": "Notes",
            "description": "Study notes and summaries",
            "link": "notes",
            "icon": "FaBookOpen"
        },
        {
            "title": "E-Books", 
            "description": "Digital books and reading materials",
            "link": "ebooks",
            "icon": "FaLaptopCode"
        },
        {
            "title": "Questions",
            "description": "Practice questions and exercises", 
            "link": "questions",
            "icon": "FaQuestion"
        },
        {
            "title": "Quiz",
            "description": "Interactive quizzes and tests",
            "link": "quiz",
            "icon": "FaQuestionCircle"
        },
        {
            "title": "Github Repos",
            "description": "Code repositories and examples",
            "link": "github",
            "icon": "FaGithub"
        }
    ]
    return resources

@app.get("/api/resources/{type}", response_model=List[ResourceContent])
async def get_resource_content(type: str):
    # Sample data - in production this would come from MongoDB
    content_map = {
        "notes": [
            {
                "id": 1,
                "title": "Python Basics",
                "content": "Introduction to Python programming language...",
                "resourceType": "notes"
            },
            {
                "id": 2,
                "title": "Advanced Python",
                "content": "Advanced concepts in Python...",
                "resourceType": "notes"
            }
        ],
        "ebooks": [
            {
                "id": 1,
                "title": "Python Programming",
                "content": "Comprehensive guide to Python programming...",
                "resourceType": "ebooks"
            }
        ],
        "questions": [
            {
                "id": 1,
                "title": "Python Practice Questions",
                "content": "Practice questions for Python programming...",
                "resourceType": "questions"
            }
        ],
        "quiz": [
            {
                "id": 1,
                "title": "Python Quiz",
                "content": "Test your Python knowledge...",
                "resourceType": "quiz"
            }
        ],
        "github": [
            {
                "id": 1,
                "title": "Python Projects",
                "content": "Collection of Python projects and examples...",
                "resourceType": "github"
            }
        ]
    }
    
    return content_map.get(type, [])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)