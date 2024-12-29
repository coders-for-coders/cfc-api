from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from bson.objectid import ObjectId

example_resources = [
    {
        "title": "",
        "content": "",
        "description": "",
        "long_description": """
  
        """,
        "type": "",
        "icon": "",
        "path": "",
    },
]

import os
import dotenv

dotenv.load_dotenv()


async def insert_example_resources():
    # Connect to MongoDB
    client = AsyncIOMotorClient(host=os.getenv("MONGODB"))
    db = client.get_database("resources")
    collection = db.resources

    # Delete existing resources
    try:
        await collection.delete_many({})
        print("Successfully deleted existing resources")
    except Exception as e:
        print(f"Error deleting resources: {e}")

    # Insert new resources
    try:
        await collection.insert_many(example_resources)
        print("Successfully inserted example resources")
    except Exception as e:
        print(f"Error inserting resources: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(insert_example_resources())
