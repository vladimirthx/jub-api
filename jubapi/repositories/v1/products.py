from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.results import DeleteResult
from bson import ObjectId
from option import Option, NONE, Some,Result,Ok,Err
from typing import List,Any,Dict
from jubapi.models.v1 import Product
from jubapi.dto.v1.product import ProductDTO

    

class ProductsRepository(object):

    def __init__(self,collection:AsyncIOMotorCollection):
        self.collection = collection

    async def create(self,product:Product)->Result[str,Exception]:
        try:
            await self.collection.insert_one(product.model_dump())
            return Ok(product.pid)
        except Exception as e:
            return Err(e)
    async def creates(self, products:List[Product]=[])->Result[Any,Exception]:
        try:
            docs = map(lambda p: p.model_dump(), products)
            res = await self.collection.insert_many(docs)
            print("RES",res)
            return Ok(None)
        except Exception as e :
            return Err(e)
        

    async def find_all(self,query:Dict[str,Any]={},skip:int=0, limit:int = 10)->List[ProductDTO]:
        cursor      = self.collection.find(query).skip(skip=skip).limit(limit=limit)
        documents = []
        async for document in cursor:
            del document["_id"]
            print(document)
            documents.append(
                ProductDTO(
                    **document
                )
            )

        await cursor.close()
        return documents

    async def find_by_pid(self,pid:str)->Option[ProductDTO]:
        res =await self.collection.find_one({"pid":pid})
        if res:
            del res["_id"]
            return Some(ProductDTO(**res))
            # return Some(CatalogDTO(**res))
        else:
            return NONE
    async def find_all_by_ids(self,ids:List[ObjectId])->List[ProductDTO]:
        cursor = self.collection.find({"_id":{"$in":ids}})
        documents=[]
        for document in cursor:
            del document["_id"]
            documents.append(
                ProductDTO(**document)
            )
        return documents
    async def filter_by_levels(
            self,tags:List[str],levels:List[str],skip:int=0, limit:int=100

    )->List[ObjectId]:
        pipeline = []
        tags   = list(filter(lambda x: len(x) >0 , tags))
        levels = list(filter(lambda x: len(x) >0 , levels))
        # print("TAGS",tags)
        if not len(tags) ==0 :
            pipeline.append(
                    {
                        "$match":{
                            "tags":{
                                "$all":tags
                            }
                        }
                    }
            )

        pipeline+=[
            {
                "$unwind": "$levels"
            },
            {
                "$group": {
                "_id": "$_id",
                "values":{"$addToSet":"$levels.value"}
                }
            },
            { "$match": { "values":{"$all":levels }}},
            {
                    "$project": {
                        "_id": 1
                    }
            },
            {
                "$skip":skip,
            },
            {
                "$limit":limit
            }
        ]
        cursor = self.collection.aggregate(pipeline=pipeline)
        documents = []
        async for document in cursor:
            documents.append(document["_id"])
        await cursor.close()
        return documents
    async def delete_by_pid(self,pid:str)->DeleteResult:
        return await self.collection.delete_one({"pid": pid})
