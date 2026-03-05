from pymongo.collection import Collection
from pymongo.results import DeleteResult
from bson import ObjectId
from pydantic import BaseModel
from uuid import uuid4
from option import Option, NONE, Some
from typing import Dict,Union,List
from jubapi.dto.v1.catalog import CatalogDTO,CatalogItemDTO
import json as J
from bson.json_util import dumps

# class CatalogItem(BaseModel):
#     name:str
#     display_name:str
#     code:str
#     description:str
#     metadata:Dict[str,str]


class RatingDTO(object):
    def __init__(self, user_id:str,observatory_id:str, value:int):
        self.value = value
        self.observatory_id = observatory_id
        self.user_id = user_id

class Rating(BaseModel):
    observatory_id:str
    value:int
    user_id:str

class RatingsRepository(object):
    def __init__(self,collection:Collection):
        self.collection = collection

    def create(self,rating:Rating):
        self.collection.insert_one(rating.model_dump())
    def find_all(self,skip:int,limit:int):
        cursor = self.collection.find({}).skip(skip=skip).limit(limit=limit)
        result = []
        for rating in cursor:
            del rating["_id"]
            result.append(rating)
        cursor.close()
        return result
            # result[observatory["key"]] ={}
            
        # return
