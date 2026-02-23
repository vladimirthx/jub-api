import os
import time as T
from typing import List
from fastapi import APIRouter,Depends
from fastapi import Response,HTTPException
# 
from jubapi.dto.observatory import ObservatoryDTO,LevelCatalogDTO
from jubapi.repositories.observatory import ObservatoriesRepository
from jubapi.db import get_collection
from jubapi.services import ObservatoriesService
from jubapi.log.log import Log
import jubapi.config as CX
log = Log(
    name                   = __name__,
    path                   = CX.JUB_LOG_PATH,
    console_handler_filter = lambda x : CX.JUB_LOG_DEBUG
)

router = APIRouter()


def get_service()->ObservatoriesService:
    collection =  get_collection(name="observatories")
    repository = ObservatoriesRepository(collection= collection)
    service = ObservatoriesService(repository= repository)
    return service



@router.post("/observatories")
async def create_observatory(
    observatory: ObservatoryDTO, 
    observatory_service:ObservatoriesService= Depends(get_service)
):
    start_time = T.time()
    exists = await observatory_service.find_by_obid(obid= observatory.obid)
    if exists.is_ok:
        return Response(content="Observatory(key={}) already exists.".format(observatory.key), status_code=403)
    observatory.image_url="https://ivoice.live/wp-content/uploads/2019/12/no-image-1.jpg"
    result = await observatory_service.create(observatory=observatory)
    if result.is_err:
        error = result.unwrap_err()
        raise HTTPException(
            status_code=400,
            detail="Observatory creation error: {}".format(error)
        )
    log.info({
        "event":"CREATE.OBSERVATORY",
        "obid":observatory.obid,
        "title":observatory.title,
        "response_time":T.time() - start_time
    })
    return { "obid": observatory.obid}


@router.delete("/observatories/{obid}")
async def delete_observatory_by_obid(obid:str, observatory_service:ObservatoriesService = Depends(get_service)):
    exists = await observatory_service.find_by_obid(obid=obid)
    if exists.is_none:
        raise HTTPException(detail="Observatory(obid={}) not found.".format(obid), status_code=404)
    else:
        response = await observatory_service.delete_by_obid(obid=obid)
        return Response(content=None, status_code=204)


@router.post("/observatories/{obid}")
async def update_catalogs_by_obid(obid:str, catalogs:List[LevelCatalogDTO]=[], observatory_service:ObservatoriesRepository = Depends(get_service)):
    if len(catalogs)==0:
        return Response(status_code=204)
    result = await observatory_service.update_catalogs(obid=obid,catalogs=catalogs)
    if result.is_err:
        raise HTTPException(status_code=500, detail="Update failted: {}".format(obid))
    return Response(status_code=204)


@router.get("/observatories")
async def get_observatories(skip:int = 0, limit:int = 10, observatory_service:ObservatoriesService = Depends(get_service)):
    documents = await observatory_service.find_all(query={"disabled":False},skip=skip,limit=limit)
    return documents

@router.get("/observatories/{obid}")
async def get_observatory_by_key(obid:str, observatory_service:ObservatoriesService = Depends(get_service)):
    # observatory       = observatories_collection.find_one({"key":key})
    observatory = await observatory_service.find_by_obid(obid=obid)
    if observatory.is_err:
        return Response(content="Observatory(key={}) not found".format(obid), status_code=404)
    return observatory.unwrap()