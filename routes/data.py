from typing import Optional

import traceback

from fastapi import APIRouter, HTTPException

from models.post import Post
from models.quiz import Question
from utils.data.mongo import MongoManager


class DataRouter:
    def __init__(self):
        self.router: APIRouter = APIRouter(prefix="/api/data")
        self.quiz: MongoManager = MongoManager("quiz_db")
        self.posts: MongoManager = MongoManager("posts_db")
        self._setup_routes()


    def _setup_routes(self):
        """
        Setup the routes for the data router.
        """
        self.router.add_api_route(
            path="/post",
            endpoint=self.get_post,
            methods=["GET"],
            response_model=list[Post] | Post,
        )

        self.router.add_api_route(
            path= "/quiz/question",
            endpoint=self.get_question,
            methods=["GET"],
            response_model=Question | list[Question]
        )

        self.router.add_api_route(
            path="/post",
            endpoint=self.create_post,
            methods=["POST"],
            response_model=dict,
        )
        self.router.add_api_route(
            path="/post",
            endpoint=self.update_post,
            methods=["PUT"],
            response_model=Post,
        )
        self.router.add_api_route(
            path="/post", 
            endpoint=self.delete_post, 
            methods=["DELETE"]
        )

    async def get_post(self, id: str | None = None, type: str | None = None) -> list[Post] | Post:
        """
        Get a post by ID or get all posts of a specific type.

        Args:
            id (Optional[str]): The ID of the post to fetch.
            type (Optional[str]): The type of posts to fetch.

        Returns:
            Union[List[Post], Post]: Either a single post or list of posts.
        """
        try:
            if id:
                post = await self.posts.get_document_by_id("posts", id)
                if not post:
                    raise HTTPException(status_code=404, detail="Post not found")
                post["id"] = str(post.pop("_id"))
                return Post(**post)
            else:
                filter = {"type": type} if type else {}
                posts = await self.posts.get_all_documents("posts", filter)
                for post in posts:
                    post["id"] = str(post.pop("_id"))
                return [Post(**post) for post in posts]
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail="Failed to fetch post" if id else "An error occurred while fetching posts"
            )

    async def create_post(self, post: Post) -> dict:
        """
        Create a new post in the database.

        Args:
            post (Post): The post data to create without ID.

        Returns:
            dict: Response containing created post ID and details
        """
        try:
            post_dict = post.model_dump(mode="json", exclude={"id"})
            created = await self.posts.create_document("posts", post_dict)
            return {
                "status": "success",
                "message": "Post created successfully",
                "id": str(created["_id"]),
                "post": {
                    "title": created["content"]["title"],
                    "type": created["metadata"]["type"],
                    "created_at": created["_id"].generation_time.isoformat()
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create resource")

    async def update_post(self, post: Post, id: Optional[str] = None) -> Post:
        """
        Update a post in the database.

        Args:
            post (Post): The updated post data.
            id (Optional[str]): The ID of the post to update.

        Returns:
            Resource: The updated resource.
        """
        try:
            if not id:
                raise HTTPException(status_code=400, detail="Post ID is required")
            post_dict = post.model_dump(mode="json", exclude={"id"})
            updated = await self.posts.update_document("posts", id, post_dict)
            updated["id"] = str(updated.pop("_id"))
            return Post(**updated)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update post")

    async def delete_post(self, id: Optional[str] = None) -> dict[str, str]:
        try:
            if not id:
                raise HTTPException(status_code=400, detail="Post ID is required")
            await self.posts.delete_document("posts", id)
            return {"message": "Post deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete post")



    async def get_question(self, id: str | None = None) -> Question | list[Question]:
        """
        Get a quiz question by ID or get all questions.

        Args:
            id (Optional[str]): The ID of the question to fetch.

        Returns:
            Union[Question, List[Question]]: Either a single question or list of questions.
        """
        try:
            if id:
                question = await self.quiz.get_document_by_id("python", id)
                if not question:
                    raise HTTPException(status_code=404, detail="Question not found")
                return Question(**question)
            else:
                questions = await self.quiz.get_all_documents("python")
                if not questions:
                    return []
                return [Question(**q) for q in questions]
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Error traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch question{'s' if not id else ''}"
            )
