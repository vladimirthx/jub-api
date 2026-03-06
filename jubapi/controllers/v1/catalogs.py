import os
import time as T
from typing import List
from fastapi import APIRouter,Depends,Response,HTTPException
from jubapi.dto.v1.catalog import CatalogDTO
from jubapi.services.v1 import CatalogsService
# 
from jubapi.repositories.v1.catalog import CatalogsRepository
from jubapi.db import get_collection
from jubapi.services.v1 import CatalogsService
from jubapi.log.log import Log
import jubapi.config as CX

log = Log(
    name                   = __name__,
    path                   = CX.JUB_LOG_PATH,
    console_handler_filter = lambda x : CX.JUB_LOG_DEBUG
)

router = APIRouter(prefix="/catalogs", tags=["catalogs"])

def get_service()->CatalogsService:
    collection = get_collection(name="catalogs")
    repository = CatalogsRepository(collection= collection)
    service    = CatalogsService(repository= repository)
    return service


@router.post(
        "",
        summary="Create a new catalog",
        description="Creates a new catalog in the database. Validates if the given catalog ID (cid) already exists to prevent duplicates. Expects a fully formed CatalogDTO object.",
        response_model=dict,
        status_code=201
)
async def create_catalogs(
    catalog:CatalogDTO, 
    catalog_service:CatalogsService= Depends(get_service) 
):
    start_time = T.time()

    exists = await catalog_service.find_by_cid(cid=catalog.cid)
    if exists.is_ok:
        raise HTTPException(
            status_code=409,
            detail=f"Catalog(cid={catalog.cid}) already exists."
        )
    
    res = await catalog_service.create(catalog=catalog)
    
    if res.is_err:
        error = res.unwrap_err()
        log.error({
            "msg":str(error)
        })
        raise error.to_http_exception()
        # raise HTTPException(status_code=500, detail="Catalog creation failed: {}".format(error))
    log.info({
        "event":"CREATE.CATALOG",
        "exists":exists.is_ok,
        "cid":catalog.cid,
        "display_name":catalog.display_name,
        "kind":catalog.kind,
        "response_time":T.time()-start_time
    })
    return { "cid": catalog.cid}


@router.delete(
        "/{cid}",
        summary="Delete a catalog",
        description="Deletes a catalog from the database using its unique Catalog ID (cid). Returns a 204 Content response on successful deletion.",
        response_model=None,
        status_code=204
)
async def delete_catalogs(cid:str, catalog_service:CatalogsService= Depends(get_service)):
    exists = await catalog_service.find_by_cid(cid=cid)
    if  exists.is_err:
        error = exists.unwrap_err()
        raise error.to_http_exception()
        # return Response(content="Catalog(key={}) not found.".format(cid), status_code=403)
    else:
        response =await catalog_service.delete_by_cid(cid=cid)
        return Response(content=None, status_code=204)

@router.get(
        "",
        summary="Retrieve all catalogs",
        description="Fetches a paginated list of all catalogs. The pagination can be controled using the \'skip\' and \'limit\' query parameters.",
        response_model=List[CatalogDTO],
        status_code=200
)
async def get_catalogs(skip:int = 0, limit:int = 10, catalog_service:CatalogsService= Depends(get_service)):
    result= await catalog_service.find_all(skip=skip,limit=limit)
    if result.is_ok:
        return result.unwrap_or([])
    error = result.unwrap_err()
    raise error.to_http_exception()

@router.get(
        "/{cid}",
        summary="Get catalog by CID",
        description="Retrieves a specific catalog's full data absed on its unique Catalog ID (cid)."
        )
async def get_catalogs_by_key(cid:str, catalog_service:CatalogsService= Depends(get_service)):
    catalog       =await catalog_service.find_by_cid(cid=cid)
    print(catalog)
    if catalog.is_err:
        error = catalog.unwrap_err()
        raise error.to_http_exception()
    return catalog.unwrap()

