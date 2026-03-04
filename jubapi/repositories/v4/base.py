from typing import TypeVar, Generic, List, Optional, Type
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from option import Result, Ok, Err
import jubapi.errors as EX
# from pymongo.collection import Collection

# T represents any of your Pydantic models (ProductX, Catalog, etc.)
T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T]):
    def __init__(self, collection: Collection, model_class: Type[T], id_field: str):
        """
        :param collection: The pymongo Collection object
        :param model_class: The Pydantic model class (e.g., ProductX)
        :param id_field: The name of the custom ID field (e.g., "product_id")
        """
        self.collection = collection
        self.model_class = model_class
        self.id_field = id_field

    async def insert(self, item: T) -> Result[str,EX.JubError]:
        """Inserts a Pydantic model into MongoDB."""
        # Convert Pydantic model to dict, excluding None values if preferred
        try: 
            item_dict = item.model_dump(mode="python")
            r = await self.collection.insert_one(item_dict)
            return Ok( getattr(item, self.id_field))
            # return getattr(item, self.id_field)
        except Exception as e:
            print(f"Error inserting item: {e}")
            return Err(EX.UnknownError(str(e)))
            # raise

    async def get_by_id(self, item_id: str) -> Result[T, EX.JubError]:
        """Fetches a single document by your custom ID field."""
        try:
            data = await self.collection.find_one({self.id_field: item_id})
            if data:
                return Ok(self.model_class(**data))
            return Err(EX.NotFound(f"Item with ID {item_id} not found"))
        except Exception as e:
            print(f"Error fetching item by ID: {e}")
            return Err(EX.UnknownError(str(e)))
    

    async def find_by_ids(self, item_ids: List[str]) -> Result[List[T], EX.JubError]:
        """Fetches multiple documents by a list of custom IDs."""
        try:
            cursor = self.collection.find({self.id_field: {"$in": item_ids}})
            return Ok([self.model_class(**doc) for doc in await cursor.to_list(length=len(item_ids))])
        except Exception as e:
            print(f"Error fetching items by IDs: {e}")
            return Err(EX.UnknownError(str(e)))
    
    async def find_many(self, query: dict, limit: int = 100) -> Result[List[T], EX.JubError]:
        """Finds multiple documents based on a standard Mongo query dictionary."""
        try:
            cursor = self.collection.find(query).limit(limit)
            return Ok([self.model_class(**doc) for doc in await cursor.to_list(length=limit)])
        except Exception as e:
            print(f"Error fetching items: {e}")
            return Err(EX.UnknownError(str(e)))

    async def delete(self, item_id: str) -> Result[bool, EX.JubError]:
        """Deletes a document by its custom ID."""
        try:
            result = await self.collection.delete_one({self.id_field: item_id})
            return Ok(result.deleted_count > 0)
        except Exception as e:
            print(f"Error deleting item: {e}")
            return Err(EX.UnknownError(str(e)))