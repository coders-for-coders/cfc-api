import os
from typing import List, Optional

from bson.objectid import ObjectId
from dotenv import load_dotenv
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
import uvicorn
from fastapi.responses import HTMLResponse

class Debug:
    enabled = False

    @classmethod
    def log(cls, message: str) -> None:
        if cls.enabled:
            print(message)

load_dotenv()

# Add error handling for MongoDB connection
try:
    mongodb_url = os.getenv("MONGODB")
    if not mongodb_url:
        raise ValueError("MONGODB environment variable not set")
    Debug.log(f"Connecting to MongoDB at: {mongodb_url}")
    client = AsyncIOMotorClient(mongodb_url)
    database = client.get_database("resources")  # Using resources_db here
    resources_collection = database.get_collection("resources")
    Debug.log(f"Connected to database: {database.name}")
    Debug.log(f"Using collection: {resources_collection.name}")
except Exception as e:
    Debug.log(f"Failed to connect to MongoDB: {str(e)}")
    raise

app = fastapi.FastAPI()

# Create a sub-application for API routes that need CORS
api_app = fastapi.FastAPI()

api_app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Add additional origins as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Resource(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    title: str
    content: str
    description: str
    long_description: str
    type: str
    icon: str
    path: str # Changed url to path to match example data


@api_app.get(path="/")
async def read_root() -> dict[str, str]:
    return {"message": "Hello, World!"}

@app.get(path="/api/docs", response_class=HTMLResponse)
async def get_docs():
    with open("docs.html") as f:
        return HTMLResponse(content=f.read())

        
@api_app.get(path="/api/resources", response_model=List[Resource])
async def get_resources(type: Optional[str] = None) -> List[Resource]:
    try:
        filter = {"type": type} if type else {}
        Debug.log(f"Fetching resources with filter: {filter}")
        resources = await resources_collection.find().to_list(length=None)
        Debug.log(f"Found {len(resources)} resources")
        
        # Convert _id to string id before creating Resource objects
        for resource in resources:
            resource['id'] = str(resource.pop('_id'))
            Debug.log(f"Processing resource: {resource['title']}")
            
        return [Resource(**resource) for resource in resources]
        
    except Exception as e:
        Debug.log(f"Error in get_resources: {str(e)}")
        raise fastapi.HTTPException(
            status_code=500,
            detail="An error occurred while fetching resources. Please try again later."
        )

@api_app.get(path="/api/resources/{id}", response_model=Resource)
async def get_resource(id: str) -> Resource:
    try:
        Debug.log(f"Fetching resource with id: {id}")
        resource = await resources_collection.find_one({"_id": ObjectId(id)})
        if not resource:
            raise fastapi.HTTPException(status_code=404, detail="Resource not found")
        # Convert _id to string id
        resource['id'] = str(resource.pop('_id'))
        Debug.log(f"Found resource: {resource['title']}")
        return Resource(**resource)
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=f"Failed to fetch resource: {str(e)}")

@api_app.post(path="/api/resources", response_model=Resource)
async def create_resource(resource: Resource) -> Resource:
    try:
        # Convert id to _id for MongoDB
        resource_dict = resource.dict()
        resource_dict['_id'] = ObjectId(resource_dict.pop('id'))
        Debug.log(f"Creating resource: {resource_dict['title']}")
        
        result = await resources_collection.insert_one(resource_dict)
        created_resource = await resources_collection.find_one({"_id": result.inserted_id})
        if not created_resource:
            raise fastapi.HTTPException(status_code=500, detail="Failed to create resource")
        # Convert _id back to string id
        created_resource['id'] = str(created_resource.pop('_id'))
        Debug.log(f"Successfully created resource with id: {created_resource['id']}")
        return Resource(**created_resource)
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=f"Failed to create resource: {str(e)}")

@api_app.put(path="/api/resources/{id}", response_model=Resource)
async def update_resource(id: str, resource: Resource) -> Resource:
    try:
        Debug.log(f"Updating resource with id: {id}")
        result = await resources_collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": resource.model_dump(exclude={"id"})}
        )
        if result.modified_count == 0:
            raise fastapi.HTTPException(status_code=404, detail="Resource not found")
            
        updated_resource = await resources_collection.find_one({"_id": ObjectId(id)})
        if not updated_resource:
            raise fastapi.HTTPException(status_code=500, detail="Failed to retrieve updated resource")
        
        # Convert _id to string id
        updated_resource['id'] = str(updated_resource.pop('_id'))    
        Debug.log(f"Successfully updated resource: {updated_resource['title']}")
        return Resource(**updated_resource)
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=f"Failed to update resource: {str(e)}")

@api_app.delete(path="/api/resources/{id}")
async def delete_resource(id: str) -> dict[str, str]:
    try:
        Debug.log(f"Deleting resource with id: {id}")
        result = await resources_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            raise fastapi.HTTPException(status_code=404, detail="Resource not found")
        Debug.log(f"Successfully deleted resource with id: {id}")
        return {"message": "Resource deleted successfully"}
    except Exception as e:
        raise fastapi.HTTPException(status_code=500, detail=f"Failed to delete resource: {str(e)}")

# Mount the API app under the main app
app.mount("/", api_app)

if __name__ == "__main__":
    Debug.enabled = True  
    uvicorn.run(app, host="0.0.0.0", port=8000)
