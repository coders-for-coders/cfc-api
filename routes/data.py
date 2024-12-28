from fastapi import APIRouter, HTTPException
from bson.objectid import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional
from utils.data.mongo import MongoManager

class Resource(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    title: str
    content: str
    description: str
    long_description: str
    type: str
    icon: str
    path: str


class DataRouter:
    """
    DataRouter class for handling data-related routes.

    Attributes:
        router (APIRouter): The FastAPI router for data routes.
        db (MongoManager): The MongoDB manager instance.
    """
    def __init__(self):
        self.router = APIRouter(prefix="/api/data")
        self.db = MongoManager()
        self._setup_routes()


    def _setup_routes(self):
        """
        Setup the routes for the data router.
        """
        self.router.add_api_route(
            path="/resources",
            endpoint=self.get_resources,
            methods=["GET"],
            response_model=List[Resource],
        )
        self.router.add_api_route(
            path="/resources",
            endpoint=self.create_resource,
            methods=["POST"],
            response_model=Resource,
        )
        self.router.add_api_route(
            path="/resources/{id}",
            endpoint=self.get_resource,
            methods=["GET"],
            response_model=Resource,
        )
        self.router.add_api_route(
            path="/resources/{id}",
            endpoint=self.update_resource,
            methods=["PUT"],
            response_model=Resource,
        )
        self.router.add_api_route(
            path="/resources/{id}", endpoint=self.delete_resource, methods=["DELETE"]
        )

    async def get_resources(self, type: Optional[str] = None) -> List[Resource]:
        """
        Get all resources of a specific type.

        Args:
            type (Optional[str]): The type of resources to fetch.

        Returns:
            List[Resource]: A list of resources.
        """
        try:
            filter = {"type": type} if type else {}
            resources = await self.db.get_all_documents("resources", filter)
            return [Resource(**resource) for resource in resources]
        except Exception as e:
            raise HTTPException(
                status_code=500, detail="An error occurred while fetching resources"
            )

    async def get_resource(self, id: str) -> Resource:
        """
        Get a resource by its ID.

        Args:
            id (str): The ID of the resource to fetch.

        Returns:
            Resource: The fetched resource.
        """
        try:
            resource = await self.db.get_document_by_id("resources", id)
            return Resource(**resource)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch resource")

    async def create_resource(self, resource: Resource) -> Resource:
        """
        Create a new resource in the database.

        Args:
            resource (Resource): The resource data to create.

        Returns:
            Resource: The created resource.
        """
        try:
            created = await self.db.create_document("resources", resource.dict())
            return Resource(**created)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create resource")

    async def update_resource(self, id: str, resource: Resource) -> Resource:
        """
        Update a resource in the database.

        Args:
            id (str): The ID of the resource to update.
            resource (Resource): The updated resource data.

        Returns:
            Resource: The updated resource.
        """
        try:
            updated = await self.db.update_document("resources", id, resource.dict())
            return Resource(**updated)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update resource")

    async def delete_resource(self, id: str) -> dict[str, str]:
        try:
            await self.db.delete_document("resources", id)
            return {"message": "Resource deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete resource")
