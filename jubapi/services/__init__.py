from jubapi.repositories.products import ProductsRepository
from jubapi.repositories.observatory import ObservatoriesRepository
from jubapi.repositories.catalog import CatalogsRepository
from option import Result,Ok,Err
from jubapi.dto.observatory import ObservatoryDTO,LevelCatalogDTO
from jubapi.dto.product import ProductDTO
from jubapi.dto import ProductFilter
from jubapi.models import LevelCatalog, Observatory,Catalog,CatalogItem,Product,Level
from jubapi.errors import JubError,AlreadyExists,NotFound,UnknownError
from  typing import List,Dict,Any
from jubapi.dto.catalog import CatalogDTO
from bson import ObjectId




class CatalogsService:

    def __init__(self,
        repository:CatalogsRepository
    ):
        self.repository = repository
    async def create(self, catalog:CatalogDTO)->Result[str, JubError]:
        try:
            model = Catalog(
                cid          = catalog.cid,
                display_name = catalog.display_name,
                items        = [ CatalogItem(**i.model_dump()) for i in catalog.items],
                kind         = catalog.kind,
            )
            x = await self.repository.create(
                catalog= model
            )
            if x.is_err:
                return Err(
                    UnknownError(
                        detail=str(x.unwrap_err())
                    )
                )
            return x
        except Exception as e:
            return Err(e)
    async def find_by_cid(self,cid:str)->Result[CatalogDTO,JubError]:
        try:
            x = await self.repository.find_by_cid(cid=cid)
            if x.is_none:
                return Err(NotFound(detail=f"Catalog(cid={cid}) not found.",))
            return Ok(x.unwrap())
        except Exception as e:
            return Err(e)
    async def find_all(self,query:Dict[str,Any]={},skip:int =0, limit:str=100)->Result[List[CatalogDTO], Exception]:
        try:
            xs = await self.repository.find_all(query=query, skip=skip, limit=limit)
            return Ok(xs)
        except Exception as e:
            return Err(e)
    async def delete_by_cid(self, cid:str)->Result[str, Exception]:
        try:
            x = await self.repository.delete_by_cid(cid=cid)
            return Ok(cid)
        except Exception as e:
            return Err(e)

    
    # async def create(self,observatory:)->Result[str,OcaError]:


class ObservatoriesService:

    def __init__(self,
        repository:ObservatoriesRepository
    ):
        self.repository = repository

    
    async def create(self,observatory:ObservatoryDTO)->Result[str,JubError]:
        try:
            exists = await self.repository.find_by_obid(obid= observatory.obid)
            if exists.is_some:
                return Err(AlreadyExists(detail="Observatory(key={}) already exists.".format(observatory.key) ))
            observatory.image_url="https://ivoice.live/wp-content/uploads/2019/12/no-image-1.jpg"
            model = Observatory(
                obid=observatory.obid,
                title= observatory.title,
                catalogs=observatory.catalogs,
                description=observatory.description,
                disabled=False,
                image_url= observatory.image_url
            )
            result = await self.repository.create(observatory=model)
            return result
        except Exception as e:
            return Err(e)
    
    async def update_catalogs(self, obid:str, catalogs: List[LevelCatalogDTO])->Result[str,JubError]:
        try:
            xs = [ LevelCatalog(cid=i.cid, level=i.level) for i in catalogs]
            x = await self.repository.update_catalogs(
                obid= obid,
                catalogs= xs
            )
            return x
        except Exception as e:
            return Err(e)
        
    async def find_by_obid(self, obid:str)->Result[ObservatoryDTO,JubError]:
        try:
            x = await self.repository.find_by_obid(obid=obid)
            if x.is_none:
                return Err(NotFound(detail="Observatory not found."))
            
            return Ok(x.unwrap())

        except Exception as e:
            return Err(e)
        
    async def find_all(self,query:Dict[str,Any] = {}, skip:int =0, limit:int =0 )->List[ObservatoryDTO]:
        return await self.repository.find_all(query=query,skip=skip,limit=limit)


class ProductsService:
    """
    Service class for managing products. Handles business logic and interactions between the ProductsRepository, ObservatoriesService, and CatalogsService.
    
    Attributes:
        repository (ProductsRepository): Repository for product data access.
        observatory_service (ObservatoriesService): Service for managing observatories, used for filtering products based on observatory catalogs.
        catalog_service (CatalogsService): Service for managing catalogs, used for retrieving catalog details during product filtering.
    """
    def __init__(
            self, 
            repository:ProductsRepository,
            observatory_service:ObservatoriesService,
            catalog_service:CatalogsService

    ):
        self.repository = repository
        self.observatory_service = observatory_service
        self.catalog_service = catalog_service
    
    async def create(self,product:ProductDTO)->Result[str, JubError]:
        """Create a new product in the system.
        Args:
            product (ProductDTO): 
                Data transfer object containing product details.
        
        Returns:
            Result: 
                - Ok (str): The unique identifier (pid) of the created product if successful.
                - Err (OcaError): An error object containing details about why the creation failed.
        Raises:
            OcaError:
                - AlreadyExists: If a product with the same pid already exists.
                - UknownError: If an unexpected error occurs during product creation.
        """
        try:
            model = Product(
                description=product.description,
                level_path=product.level_path,
                levels=[ Level(**p.model_dump()) for p in product.levels],
                pid=product.pid,
                product_name=product.product_name,
                product_type=product.product_type,
                profile=product.profile,
                tags=product.tags,
                url=product.url
                # **product.model_dump()
            )
            x = await self.repository.create(product=model)
            if x.is_err:
                return Err(UnknownError(detail="Product creation failed"))
            return Ok(product.pid)
        except Exception as e:
            return Err(e)
    async def create_many(self, products:List[ProductDTO]=[])->Result[List[str], JubError]:
        try:
            xs = list(map(lambda x : Product(**x.model_dump()), products))
            res = await self.repository.creates(products=xs)
            if res.is_err:
                return Err(UnknownError(detail="Products creation failed."))
            return Ok(list(map(lambda x :x.pid, products)))
        except Exception as e:
            return Err(e)
    async def find_by_pid(self, pid:str)->Result[ProductDTO, JubError]:
        try:
            xs = await self.repository.find_by_pid(pid=pid)
            if xs.is_none:
                return Err(NotFound(detail="Product not found."))
            return Ok(xs.unwrap())
        except Exception as e:
            return Err(UnknownError(detail=str(e)))
    
    async def find_all(self, query:Dict[str,Any]={}, skip:int =0, limit:int = 100)->Result[List[ProductDTO], JubError]:
        try:
            xs = await self.repository.find_all(query=query, skip=skip,limit=limit)
            return Ok(xs)
        except Exception as e:
            return Err(UnknownError(detail=str(e)))
    async def find_all_by_ids(self, ids:List[ObjectId])->Result[List[ProductDTO],JubError]:
        try:
            xs = await self.repository.find_all_by_ids(ids=ids)
            return Ok(xs)
        except Exception as e:
            return Err(UnknownError(detail=str(e)))
    async def filter_by_levels(self,tags:List[str],levels:List[str],skip:int=0, limit:int=100)->Result[List[ObjectId], JubError]:
        try:
            xs = await self.repository.filter_by_levels(tags=tags,levels=levels, skip=skip, limit=limit)
            return Ok(xs)
        except Exception as e:
            return Err(UnknownError(detail=str(e)))
    async def delete_by_pid(self, pid:str)->Result[str, JubError]:
        try:
            x = await self.repository.delete_by_pid(pid=pid)
            return Ok(pid)
        except Exception as e:
            return Err(UnknownError(detail=str(e)))
    async def filter(
        self,
        obid:str,
        filters:ProductFilter,
        skip:int =0,
        limit:int = 100, 
    )->List[ProductDTO]:
        result = await self.observatory_service.find_by_obid(obid=obid)
        if result.is_err:
            error = result.unwrap_err()
            raise error
        observatory = result.unwrap()
        catalogs:List[CatalogDTO] = []
        for catalog in observatory.catalogs:
            _catalog = await self.catalog_service.find_by_cid(cid=catalog.cid)
            if _catalog.is_err:
                error = _catalog.unwrap_err()
                raise error
                # raise HTTPException(status_code=500, detail="Catalog(cid={}) not found".format(catalog.cid))
            c = _catalog.unwrap()
            catalogs.append(c)
        
        temporal_catalog = next(filter(lambda x: x.kind=="TEMPORAL", catalogs),None)
        spatial_catalog = next(filter(lambda x: x.kind=="SPATIAL", catalogs),None)
        interest_catlaog = next(filter(lambda x: x.kind=="INTEREST", catalogs),None)

        pipeline = []
        tags=filters.tags
        if not len(tags) ==0 :
            pipeline.append(
                    {
                        "tags":{
                            "$all":tags
                        }
                    }
            )
        temporal_vals= []


        if (not temporal_catalog == None) and  (not filters.temporal == None):
            for e in temporal_catalog.items:
                v = int(e.value)
                if v >= filters.temporal.low and v <= filters.temporal.high:
                    temporal_vals.append(str(v))
            temporal_match =    {
                        'levels': {
                            '$elemMatch': {
                                'kind': 'TEMPORAL',
                                'value': {'$in': temporal_vals}
                            }
                        }
            }
            pipeline.append(temporal_match)
        if (not spatial_catalog == None) and (not filters.spatial == None):

            spatial_regex = filters.spatial.make_regex()
            spatial_match = {
                "levels.value":{
                    "$regex":spatial_regex
                }
            }

            pipeline.append(spatial_match)
        # print(interest_catlaog)
        if (not interest_catlaog == None) and not (len(filters.interest) == 0):
            for interest in filters.interest:
                print("INTEREST",interest)
                if not interest.value  == None:
                    x = {
                        "levels":{
                            "$elemMatch":{
                                "kind":"INTEREST",
                                "value":{"$in":[interest.value]}
                            }
                        }
                    }
                    pipeline.append(x)
                if not interest.inequality == None:
                    x = {
                            "levels":{
                                "$elemMatch":{
                                    "kind":"INTEREST_NUMERIC",
                                    "value":{
                                        "$gt":str(interest.inequality.gt),
                                        "$lt":str(interest.inequality.lt)
                                    }
                                }
                            }
                    }
                    pipeline.append(x)

                    

        if len(pipeline) == 0:
            _pipeline = [{"$match":{}}]
        else:
            _pipeline = [
                {
                    "$match":{
                        "$and":pipeline
                    }
                }
            ]
        
        # print(jsonable_encoder(_pipeline))
        curosr =  self.repository.collection.aggregate(pipeline=_pipeline)
        documents = []
        async for document in curosr:
            del document["_id"]
            documents.append(ProductDTO(**document))
        return documents

    # from jubapi.dto.observatory import ObservatoryDTO,LevelCatalogDTO
