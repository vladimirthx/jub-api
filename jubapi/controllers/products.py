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
from jubapi.dto.catalog import CatalogDTO
from jubapi.dto import ProductFilter
# CatalogsService
from jubapi.log.log import Log
LOG_DEBUG = bool(int(os.environ.get("LOG_DEBUG","1")))
log = Log(
    name=os.environ.get("PRODUCTS_LOG_NAME","oca_products"),
    path=os.environ.get("JUB_LOG_PATH","/log"),
    console_handler_filter= lambda x : LOG_DEBUG
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
# def get_observatory_service()->ObservatoriesService:
#     return service
# def get_catalog_service()->ObservatoriesService:
    # return service

# Products
@router.get("/products")
async def get_products(skip:int =0, limit:int = 100, product_service: ProductsService = Depends(get_service)):
    documents = await product_service.find_all(skip=skip,limit=limit)
    print(documents)
    if documents.is_err:
        error = documents.unwrap_err()
        raise error
    return documents.unwrap()

@router.get("/products/{pid}")
async def get_product_by_pid(pid:str,product_service: ProductsService = Depends(get_service)):
    documents = await product_service.find_by_pid(pid=pid)
    if documents.is_err:
        error = documents.unwrap_err()
        raise error
    return documents.unwrap()



@router.post("/observatories/{obid}/products/nid")
# @router.post("/f/products/{obid}")
async def get_products_by_filter(
    obid:str,
    filters:ProductFilter,
    skip:int =0,
    limit:int = 100, 
    product_service: ProductsService = Depends(get_service),
    # observatory_service:ObservatoriesService = Depends(get_observatory_service),
    # catalog_service:CatalogsService = Depends(get_catalog_service)
):
    xs = await product_service.filter(
        obid=obid,
        filters=filters,
        skip=skip,
        limit=limit

    )
    return xs
    # result = await observatory_service.find_by_obid(obid=obid)
    # if result.is_err:
    #     error = result.unwrap_err()
    #     raise error
    
    # observatory = result.unwrap()
    # catalogs:List[CatalogDTO] = []
    # for catalog in observatory.catalogs:
    #     _catalog = await catalog_service.find_by_cid(cid=catalog.cid)
    #     if _catalog.is_err:
    #         error = _catalog.unwrap_err()
    #         raise error
    #         # raise HTTPException(status_code=500, detail="Catalog(cid={}) not found".format(catalog.cid))
    #     c = _catalog.unwrap()
    #     catalogs.append(c)
    
    # temporal_catalog = next(filter(lambda x: x.kind=="TEMPORAL", catalogs),None)
    # spatial_catalog = next(filter(lambda x: x.kind=="SPATIAL", catalogs),None)
    # interest_catlaog = next(filter(lambda x: x.kind=="INTEREST", catalogs),None)

    # pipeline = []
    # tags=filters.tags
    # if not len(tags) ==0 :
    #     pipeline.append(
    #             {
    #                 "tags":{
    #                     "$all":tags
    #                 }
    #             }
    #     )
    # temporal_vals= []


    # if (not temporal_catalog == None) and  (not filters.temporal == None):
    #     for e in temporal_catalog.items:
    #         v = int(e.value)
    #         if v >= filters.temporal.low and v <= filters.temporal.high:
    #             temporal_vals.append(str(v))
    #     temporal_match =    {
    #                 'levels': {
    #                     '$elemMatch': {
    #                         'kind': 'TEMPORAL',
    #                         'value': {'$in': temporal_vals}
    #                     }
    #                 }
    #     }
    #     pipeline.append(temporal_match)
    # if (not spatial_catalog == None) and (not filters.spatial == None):

    #     spatial_regex = filters.spatial.make_regex()
    #     spatial_match = {
    #         "levels.value":{
    #             "$regex":spatial_regex
    #         }
    #     }

    #     pipeline.append(spatial_match)
    # # print(interest_catlaog)
    # if (not interest_catlaog == None) and not (len(filters.interest) == 0):
    #     for interest in filters.interest:
    #         print("INTEREST",interest)
    #         if not interest.value  == None:
    #             x = {
    #                 "levels":{
    #                     "$elemMatch":{
    #                         "kind":"INTEREST",
    #                         "value":{"$in":[interest.value]}
    #                     }
    #                 }
    #             }
    #             pipeline.append(x)
    #         if not interest.inequality == None:
    #             x = {
    #                     "levels":{
    #                         "$elemMatch":{
    #                             "kind":"INTEREST_NUMERIC",
    #                             "value":{
    #                                 "$gt":str(interest.inequality.gt),
    #                                 "$lt":str(interest.inequality.lt)
    #                             }
    #                         }
    #                     }
    #             }
    #             pipeline.append(x)

                

    # if len(pipeline) == 0:
    #     _pipeline = [{"$match":{}}]
    # else:
    #     _pipeline = [
    #         {
    #             "$match":{
    #                 "$and":pipeline
    #             }
    #         }
    #     ]
    
    # # print(jsonable_encoder(_pipeline))
    # curosr =  product_service.repository.collection.aggregate(pipeline=_pipeline)
    # documents = []
    # async for document in curosr:
    #     del document["_id"]
    #     documents.append(document)
    # return JSONResponse(
    #     content= jsonable_encoder(documents)
    # )

@router.post("/products")
async def create_products(products:List[ProductDTO], product_service: ProductsService = Depends(get_service)):
    start_time = T.time()
    res = await product_service.create_many(products=products)
    if res.is_err:
        raise HTTPException(status_code= 500, detail=f"Failed to create products. {res.unwrap_err()}")
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
        raise error
        # raise HTTPException(detail="Product(pid={}) not found.".format(pid), status_code=404)
    else:
        response = await product_service.delete_by_pid(pid=pid)
        return Response(content=None, status_code=204)
