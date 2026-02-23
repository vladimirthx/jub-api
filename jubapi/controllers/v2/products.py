import os
import time as T
from typing import List
from fastapi import APIRouter,Depends
from fastapi import Response,HTTPException
from jubapi.db import get_collection
from jubapi.log.log import Log
from jubapi.services.v2 import ProductsService
from jubapi.repositories.v2 import ProductRepository
from jubapi.dto.v2 import ProductDTO
from jubapi.querylang.dto import  ProductCreationDTO

LOG_DEBUG = bool(int(os.environ.get("LOG_DEBUG","1")))
log = Log(
    name=os.environ.get("CATALOGS_LOG_NAME","oca_product_v2"),
    path=os.environ.get("JUB_LOG_PATH","/log"),
    console_handler_filter= lambda x : LOG_DEBUG
)
router = APIRouter(prefix="/v2/products")


def get_service()->ProductsService:
    collection =  get_collection(name="productsv2")
    repository = ProductRepository(collection= collection)
    service = ProductsService(repository= repository)
    return service

@router.post("/x")
async def create_productx(
    observatory:ProductCreationDTO,
    product_service:ProductsService = Depends(get_service)
):
    x = await product_service.create(
        product=observatory
    )

    if x.is_err:
        raise x.unwrap_err()
    return { "pid": x.unwrap()}
@router.post("/")
async def create_product(
    observatory:ProductDTO,
    product_service:ProductsService = Depends(get_service)
):
    x = await product_service.create(
        product=observatory
    )

    if x.is_err:
        raise x.unwrap_err()
    return { "pid": x.unwrap()}