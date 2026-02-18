import os
import time as T
from typing import List
from fastapi import APIRouter,Depends
from fastapi import Response,HTTPException
from jubapi.db import get_collection
from jubapi.log.log import Log
from jubapi.services.v2 import ObservatoriesService
from jubapi.repositories.v2 import ObservatoriesRepository
from jubapi.dto.v2 import ObservatoryDTO

LOG_DEBUG = bool(int(os.environ.get("LOG_DEBUG","1")))
log = Log(
    name=os.environ.get("CATALOGS_LOG_NAME","oca_observatory_v2"),
    path=os.environ.get("JUB_LOG_PATH","/log"),
    console_handler_filter= lambda x : LOG_DEBUG
)
router = APIRouter(prefix="/v2/observatories")


def get_service()->ObservatoriesService:
    collection =  get_collection(name="observatoriesv2")
    repository = ObservatoriesRepository(collection= collection)
    service = ObservatoriesService(repository= repository)
    return service


@router.post("/")
async def create_observatory(
    observatory:ObservatoryDTO,
    observatory_service:ObservatoriesService = Depends(get_service)
):
    x = await observatory_service.create(
        observatory=observatory
    )

    if x.is_err:
        raise x.unwrap_err()
    return { "obid": x.unwrap()}