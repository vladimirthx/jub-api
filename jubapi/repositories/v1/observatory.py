# from pymongo.collection import Collection
from pymongo.results import DeleteResult
from motor.motor_asyncio import AsyncIOMotorCollection
from option import NONE, Option,Some,Result,Ok,Err
from typing import List,Any,Dict
import string as S
from nanoid import generate as nanoid
from jubapi.dto.observatory import ObservatoryDTO,LevelCatalogDTO
from jubapi.utils.utils import Utils as U
from jubapi.models import Observatory,LevelCatalog



class ObservatoriesRepository(object):

    def __init__(self,collection:AsyncIOMotorCollection):
        self.collection = collection

    async def update_catalogs(
            self,
            obid:str,
            catalogs:List[LevelCatalog]=[]
    )->Result[str,Exception]:
        try:
            _catalogs = list(map(lambda x: x.model_dump() , catalogs))
            result= await self.collection.update_one({
                "obid":obid
            }, {
                "$set":{"catalogs": _catalogs  }
            })
            return Ok(obid)
        except Exception as e:
            return Err(e)
        
    async def create(self,observatory:Observatory)->Result[str, Exception]:
        try:
            if observatory.obid == "":
                observatory.obid = nanoid(alphabet=S.ascii_lowercase+S.digits,size=24)
            if not U.check_string(observatory.obid):
                return Err(Exception("Obid({}) is not valid".format(observatory.obid)))
            
            db_res = await self.collection.insert_one(observatory.model_dump())
            return Ok(observatory.obid)
        except Exception as e:
            return Err(e)

    async def find_all(self,query:Dict[str,Any]={},skip:int=0, limit:int = 10)->List[ObservatoryDTO]:
        cursor       = self.collection.find(query).skip(skip=skip).limit(limit=limit)
        result:List[ObservatoryDTO] = []
        async for observatory in cursor:
            del observatory["_id"]
            result.append(ObservatoryDTO(
                obid= observatory["obid"],
                title = observatory["title"],
                image_url= observatory.get("image_url",""),
                description = observatory.get("description","..."),
                catalogs= list ( map(lambda x: LevelCatalogDTO(**x),observatory["catalogs"]))
            ))
        await cursor.close()
        return result
    async def find_by_obid(self,obid:str)->Option[ObservatoryDTO]:
        try: 
            res = await self.collection.find_one({"obid":obid})
            if res:
                del res["_id"]
                catalogs = list(map(lambda x: LevelCatalogDTO(**x),res.get("catalogs",[])))
                result = Some(
                    ObservatoryDTO(
                        obid=res.get("obid","KEY"),
                        title=res.get("title","Titulo del Observatorio"),
                        image_url=res.get("image_url",""),
                        catalogs=catalogs,
                        description=res.get("description","Sin descripción por el momento."),
                    )
                )
                return result
            else:
                return NONE
        except Exception as e:
            print(e)
            return None

    def delete_by_obid(self,obid:str)->DeleteResult:
        return self.collection.delete_one({"obid": obid})
