import os
import time as T
from typing import List,Optional
from jubapi.db import connect_to_mongo,get_collection
from fastapi import APIRouter,Depends,Request
from fastapi import Response,HTTPException
from jubapi.db import get_collection
from jubapi.log.log import Log
from jubapi.services.v2 import ObservatoriesService,ProductsService,OcaNameService
from jubapi.repositories.v2 import ProductRepository,XVariablesRepository,XVariableAssignmentRepository
from jubapi.dto.v2 import ObservatoryDTO
from pydantic import BaseModel
from jubapi.querylang.peg import grammar
import json as J
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

LOG_DEBUG = bool(int(os.environ.get("LOG_DEBUG","1")))
log = Log(
    name=os.environ.get("CATALOGS_LOG_NAME","oca_observatory_v2"),
    path=os.environ.get("JUB_LOG_PATH","/log"),
    console_handler_filter= lambda x : LOG_DEBUG
)
router = APIRouter(prefix="/v2/nameservice")

templates = Jinja2Templates(directory="templates")

class InputQuery(BaseModel):
    input: str

class InputQueryX(BaseModel):
    sv: Optional[str]="*"
    tv: Optional[str] ="*"
    iv: Optional[str] ="*"
    pt: Optional[str] ="*"


async def get_nameservice():
    # Setup: Connect to MongoDB and get the collection
    _                          = await connect_to_mongo()
    c                          = get_collection(name="productsv2")
    product_repository                 = ProductRepository(collection=c)
    xvar_repo                  = XVariablesRepository(collection=get_collection("xvariables"))
    xvariable_assignments_repo = XVariableAssignmentRepository(collection=get_collection("xvariable_assignments"))
    product_service            = ProductsService(
        repo                  = product_repository,
        xvar_assignments_repo = xvariable_assignments_repo,
        xvar_repo             = xvar_repo
    )
    oca_nameservice = OcaNameService(
        xvariable_assignments_repo = xvariable_assignments_repo,
        product_repo= product_repository
    )
    
    return oca_nameservice

# @router.get("/", response_class=HTMLResponse)
# async def get_form(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

@router.post("/")
def interpret(input_query:InputQuery):
    result = grammar.parseString(input_query.input)
    res_json =result.asDict()
    return res_json

@router.post("/qx")
async def interpret(
    query: InputQueryX,  
    service:OcaNameService = Depends(get_nameservice)
):
    input: str
    # result = grammar.parseString(input_query.input)
    # res_json =result.asDict()
    xs = await service.filter(
        query=f"""
            SV = {query.sv}
            TV = {query.tv}
            IV = {query.iv}
            PT = {query.pt}
        """
    )
    return xs



# def get_service()->ObservatoriesService:
#     collection =  get_collection(name="observatoriesv2")
#     repository = ObservatoriesRepository(collection= collection)
#     service = ObservatoriesService(repository= repository)
#     return service