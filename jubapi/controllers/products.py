import os
import time as T
from typing import List
from fastapi import APIRouter,Depends,Response,HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from jubapi.repositories.products import ProductsRepository
from jubapi.repositories.observatory import ObservatoriesRepository
from jubapi.repositories.catalog import CatalogsRepository
from jubapi.db import get_collection
from jubapi.services import ProductsService,ObservatoriesService,CatalogsService
from jubapi.dto.product import ProductDTO
from jubapi.dto import ProductFilter
from jubapi.log.log import Log
import jubapi.config as CX
# LOG_DEBUG = bool(int(os.environ.get("LOG_DEBUG","1")))
log = Log(
    name                   = __name__,
    path                   = CX.JUB_LOG_PATH,
    console_handler_filter = lambda x : CX.JUB_LOG_DEBUG
)

router = APIRouter()


def get_service()->ProductsService:
    collection =  get_collection(name="products")
    repository = ProductsRepository(collection= collection)
    # 
    collection =  get_collection(name="observatories")
    repository1 = ObservatoriesRepository(collection= collection)
    service1 = ObservatoriesService(repository= repository1)
    # 
    collection =  get_collection(name="catalogs")
    repository2 = CatalogsRepository(collection= collection)
    service2 = CatalogsService(repository= repository2)
    # 
    service = ProductsService(repository= repository,catalog_service=service2,observatory_service=service1)
    return service



# Products
@router.get("/products")
async def get_products(skip:int =0, limit:int = 100, product_service: ProductsService = Depends(get_service))->List[ProductDTO]:
    """
    Retrieve a list of products with optional pagination.

    - **skip**: Number of items to skip (default is 0)
    - **limit**: Maximum number of items to return (default is 100)
    """
    documents = await product_service.find_all(skip=skip,limit=limit)
    if documents.is_err:
        error = documents.unwrap_err()
        raise error.to_http_exception()
    return documents.unwrap()

@router.get("/products/{pid}")
async def get_product_by_pid(pid:str,product_service: ProductsService = Depends(get_service))->ProductDTO:
    documents = await product_service.find_by_pid(pid=pid)
    if documents.is_err:
        error = documents.unwrap_err()
        raise error.to_http_exception()
    return documents.unwrap()



@router.post("/observatories/{obid}/products/nid")
# @router.post("/f/products/{obid}")
async def get_products_by_filter(
    obid:str,
    filters:ProductFilter,
    skip:int =0,
    limit:int = 100, 
    product_service: ProductsService = Depends(get_service),
)->List[ProductDTO]:
    xs = await product_service.filter(
        obid=obid,
        filters=filters,
        skip=skip,
        limit=limit

    )
    return xs


@router.post("/products")
async def create_products(products:List[ProductDTO], product_service: ProductsService = Depends(get_service)):
    start_time = T.time()
    res = await product_service.create_many(products=products)
    if res.is_err:
        error = res.unwrap_err()
        raise error.to_http_exception()
    service_time = T.time() - start_time
    log.info({
        "event":"CREATE.PRODUCTS",
        "n":len(products)
    })
    return Response(content=None,status_code=201,)



@router.delete("/products/{pid}")
async def delete_product_by_pid(pid:str,product_service: ProductsService = Depends(get_service)):
    exists = await product_service.find_by_pid(pid=pid)
    if exists.is_err:
        error = exists.unwrap_err()
        raise error.to_http_exception()
        # raise HTTPException(detail="Product(pid={}) not found.".format(pid), status_code=404)
    else:
        response = await product_service.delete_by_pid(pid=pid)
        return Response(content=None, status_code=204)
