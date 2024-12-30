from fastapi import APIRouter, HTTPException
from bson.objectid import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional
from utils.data.mongo import MongoManager
from random import randrange

class Resource(BaseModel):
    id: str
    title: str
    content: str
    description: str
    long_description: str
    type: str
    icon: str
    path: str

class Question(BaseModel):
    id: str
    question: str
    options: list[dict[str,str]]
    answer: str


class DataRouter:
    """
    DataRouter class for handling data-related routes.

    Attributes:
        router (APIRouter): The FastAPI router for data routes.
        db (MongoManager): The MongoDB manager instance.
    """
    def __init__(self):
        self.router = APIRouter(prefix="/api/data")
        self.resources = MongoManager("resources")
        self.quiz = MongoManager("quiz")
        self._setup_routes()


    def _setup_routes(self):
        """
        Setup the routes for the data router.
        """
        self.router.add_api_route(
            path="/resource",
            endpoint=self.get_resource,
            methods=["GET"],
            response_model=List[Resource] | Resource,
        )

        self.router.add_api_route(
            path= "/quiz/question",
            endpoint=self.get_question,
            methods=["GET"],
            response_model=Question | list[Question]
        )
        # TODO - commented methods need to be fixed

        # self.router.add_api_route(
        #     path="/resource",
        #     endpoint=self.create_resource,
        #     methods=["POST"],
        #     response_model=dict,
        # )
        # self.router.add_api_route(
        #     path="/resource",
        #     endpoint=self.update_resource,
        #     methods=["PUT"],
        #     response_model=Resource,
        # )
        # self.router.add_api_route(
        #     path="/resource", 
        #     endpoint=self.delete_resource, 
        #     methods=["DELETE"]
        # )

    async def get_resource(self, id: Optional[str] = None, type: Optional[str] = None) -> List[Resource] | Resource:
        """
        Get a resource by ID or get all resources of a specific type.

        Args:
            id (Optional[str]): The ID of the resource to fetch.
            type (Optional[str]): The type of resources to fetch.

        Returns:
            Union[List[Resource], Resource]: Either a single resource or list of resources.
        """
        try:
            if id:
                resource = await self.resources.get_document_by_id("resources", id)
                return Resource(**resource)
            else:
                filter = {"type": type} if type else {}
                resources = await self.resources.get_all_documents("resources", filter)
                return [Resource(**resource) for resource in resources]
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail="Failed to fetch resource" if id else "An error occurred while fetching resources"
            )

    # async def create_resource(self, resource: Resource) -> dict:
    #     """
    #     Create a new resource in the database.

    #     Args:
    #         resource (Resource): The resource data to create.

    #     Returns:
    #         dict: Response containing created resource ID and details
    #     """
    #     try:
    #         created = await self.resources.create_document("resources", resource.model_dump(mode="json"))
    #         return {
    #             "status": "success",
    #             "message": "Resource created successfully",
    #             "id": str(created["_id"]),
    #             "resource": {
    #                 "title": created["title"],
    #                 "type": created["type"],
    #                 "created_at": created.get("_id").generation_time.isoformat()
    #             }
    #         }
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=f"Failed to create resource")

    # async def update_resource(self, resource: Resource, id: Optional[str] = None) -> Resource:
    #     """
    #     Update a resource in the database.

    #     Args:
    #         resource (Resource): The updated resource data.
    #         id (Optional[str]): The ID of the resource to update.

    #     Returns:
    #         Resource: The updated resource.
    #     """
    #     try:
    #         if not id:
    #             raise HTTPException(status_code=400, detail="Resource ID is required")
    #         updated = await self.resources.update_document("resources", id, resource.dict())
    #         return Resource(**updated)
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=f"Failed to update resource")

    # async def delete_resource(self, id: Optional[str] = None) -> dict[str, str]:
    #     try:
    #         if not id:
    #             raise HTTPException(status_code=400, detail="Resource ID is required")
    #         await self.resources.delete_document("resources", id)
    #         return {"message": "Resource deleted successfully"}
    #     except Exception as e:
    #         raise HTTPException(status_code=500, detail=f"Failed to delete resource")

    async def get_question(self) -> Question | list[Question]:

        data = await self.quiz.get_all_documents("quiz")

        # question = Quiz(**data)

        print(data)

        return {}

