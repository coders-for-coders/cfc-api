import os
from typing import Dict, List, Optional

from bson.objectid import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

class MongoManager:
    _instance = None
    _client: Optional[AsyncIOMotorClient] 
    _database: Optional[AsyncIOMotorDatabase] 
    _collections: Dict[str, AsyncIOMotorCollection] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_client'):
            self._initialize_connection()

    def _initialize_connection(self):
        mongodb_url = os.getenv("MONGODB")
        if not mongodb_url:
            raise ValueError("MONGODB environment variable not set")
            
        self._client = AsyncIOMotorClient(mongodb_url)
        self._database = self._client.get_database("cfc_db")

    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            raise ValueError("MongoDB client not initialized")
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise ValueError("MongoDB database not initialized")
        return self._database

    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        if collection_name not in self._collections:
            if self._database is None:
                raise ValueError("MongoDB database not initialized")
            self._collections[collection_name] = self._database.get_collection(collection_name)
        return self._collections[collection_name]

    async def get_all_documents(self, collection_name: str, filter_query: Optional[dict] = None) -> List[dict]:
        try:
            collection = self.get_collection(collection_name)
            documents = await collection.find(filter_query or {}).to_list(length=None)
            for doc in documents:
                doc['id'] = str(doc.pop('_id'))
            return documents
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch documents: {str(e)}")

    async def get_document_by_id(self, collection_name: str, id: str) -> dict:
        try:
            collection = self.get_collection(collection_name)
            document = await collection.find_one({"_id": ObjectId(id)})
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            document['id'] = str(document.pop('_id'))
            return document
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch document: {str(e)}")

    async def create_document(self, collection_name: str, document_data: dict) -> dict:
        try:
            collection = self.get_collection(collection_name)
            document_data['_id'] = ObjectId(document_data.pop('id', None))
            result = await collection.insert_one(document_data)
            created = await collection.find_one({"_id": result.inserted_id})
            if not created:
                raise HTTPException(status_code=500, detail="Failed to create document")
            created['id'] = str(created.pop('_id'))
            return created
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")

    async def update_document(self, collection_name: str, id: str, document_data: dict) -> dict:
        try:
            collection = self.get_collection(collection_name)
            update_data = {k: v for k, v in document_data.items() if k != 'id'}
            result = await collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": update_data}
            )
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Document not found")
            
            updated = await collection.find_one({"_id": ObjectId(id)})
            if not updated:
                raise HTTPException(status_code=500, detail="Failed to retrieve updated document")
            updated['id'] = str(updated.pop('_id'))
            return updated
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")

    async def delete_document(self, collection_name: str, id: str) -> bool:
        try:
            collection = self.get_collection(collection_name)
            result = await collection.delete_one({"_id": ObjectId(id)})
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Document not found")
            return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            self._collections = {}