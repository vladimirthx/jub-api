from typing import Optional,List
from pydantic import BaseModel
class LevelCatalogDTO(BaseModel):
    level:int
    cid:str
class ObservatoryDTO(BaseModel):
    obid:Optional[str]=""
    title:str
    image_url:Optional[str]=""
    description:str
    catalogs:Optional[List[LevelCatalogDTO]] =[]
        