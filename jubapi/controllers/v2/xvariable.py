import os
import time as T
from typing import List
from fastapi import APIRouter,Depends
from jubapi.db import get_collection
from jubapi.log.log import Log
from jubapi.services.v2 import XVariablesService,XVariableAssignmentsService
from jubapi.repositories.v2 import XVariablesRepository,XVariableAssignmentRepository
from jubapi.dto.v2 import XVariableDTO,MultipleXVariableAssignmentDTO,ManyProductsMultipleXVariableAssignmentDTO

LOG_DEBUG = bool(int(os.environ.get("LOG_DEBUG","1")))
log = Log(
    name=os.environ.get("CATALOGS_LOG_NAME","oca_observatory_v2"),
    path=os.environ.get("JUB_LOG_PATH","/log"),
    console_handler_filter= lambda x : LOG_DEBUG
)
router = APIRouter(prefix="/v2/xvariables")


def get_service()->XVariablesService:
    collection =  get_collection(name="xvariables")
    repository = XVariablesRepository(collection= collection)
    service = XVariablesService(repo= repository)
    return service
def get_service_assign()->XVariablesService:
    collection =  get_collection(name="xvariablesassignments")
    repository = XVariableAssignmentRepository(collection= collection)
    service = XVariableAssignmentsService(repo= repository)
    return service


@router.post("/")
async def create_xvariable(
    xvariables:List[XVariableDTO],
    xvariable_service:XVariablesService = Depends(get_service)
):
    xvids = []
    for y in xvariables:
        x = await xvariable_service.create(
            xvariable=y
        )
        if x.is_err:
            raise x.unwrap_err()
        xvids.append(x.unwrap())
    return { "xvids": xvids }


@router.post("/assign")
async def assign_xvariable(
    dto:MultipleXVariableAssignmentDTO,
    xvariables_assign_service: XVariableAssignmentsService = Depends(get_service_assign)
):
    x = await xvariables_assign_service.assign(dto=dto)
    
    if x.is_err:
        raise x.unwrap_err()
    return x.unwrap()

    