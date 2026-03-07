
from option import Result,Ok,Err
from  typing import List,Dict,Any
# 
from jubapi.repositories.v1.products import ProductsRepository
from jubapi.repositories.v1.observatory import ObservatoriesRepository
from jubapi.repositories.v1.catalog import CatalogsRepository
from jubapi.dto.v1.observatory import ObservatoryDTO,LevelCatalogDTO
from jubapi.dto.v1.product import ProductDTO
from jubapi.dto.v1.catalog import CatalogDTO
from jubapi.dto.v1 import ProductFilter
from jubapi.models.v1 import LevelCatalog, Observatory,Catalog,CatalogItem,Product,Level
from jubapi.errors import JubError,AlreadyExists,NotFound,UnknownError
from bson import ObjectId




class CatalogsService:
    """
    Service responsible for managing Catalog business logic.
    Provides methods to create, retrieve, and delete catalogs and their embedded items.
    """

    def __init__(self,
        repository:CatalogsRepository
    ):
        """
        Initializes the CatalogsService.

        Args:
            respository (CatalogsRepository): The data access layer for catalogs.
        """

        self.repository = repository
    async def create(self, catalog:CatalogDTO)->Result[str, JubError]:
        """
        Registers a new catalog into the system along with its items.

        This method maps the incoming DTO into the internal database model,
        ensuring all embedded items are properly cast to CatalogItem instances.

        Args:
            catalog (CatalogDTO): The data transfer object containing the new catalog's definitions.

        Returns:
            Result[str,JubError]: An 'Ok' wrapping the newly created Catalog ID (cid) if successful,
            or an 'Err' wrapping a JubError if the insertion fails. 
        """

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
        """
        Retrieves a catalog's full details by its unique Catalog ID.

        Args:
            cid (str): The unique identifier of the catalog to search for.

        Returns:
            Result[CatalogDTO, OcaError]: An 'Ok' containing the CatalogDTO if found,
            or an 'Err' wrapping a NotFound error if it does not exist.
        """

        try:
            x = await self.repository.find_by_cid(cid=cid)
            if x.is_none:
                return Err(NotFound(detail=f"Catalog(cid={cid}) not found.",))
            return Ok(x.unwrap())
        except Exception as e:
            return Err(e)
    async def find_all(self,query:Dict[str,Any]={},skip:int =0, limit:str=100)->Result[List[CatalogDTO], Exception]:
        """
        Fetches a paginated list of catalogs matching the provided query filters.

        Args:
            query (Dict[str,Any], optional): MongoDB filter criteria. Defaults to {}.
            skip (int, optional): Number of documents to skip for pagination. Defaults to 0.
            limit (str, optional): Maximum number of documents to return. Defaults to 100.

        Returns:
            Result[List[CatalogDTO], Exception]: An 'Ok' wrapping the list of matching catalogs,
            or an 'Err' if a database exception occurs.

        """
        try:
            xs = await self.repository.find_all(query=query, skip=skip, limit=limit)
            return Ok(xs)
        except Exception as e:
            return Err(e)
    async def delete_by_cid(self, cid:str)->Result[str, Exception]:
        """
        Permanently removes a catalog from the database using its ID.

        Args:
            cid(str): THe unique identifier of the catalog to delete.

        Returns:
            Result[str, Exception]: An 'Ok' with the deleted cid if successful, or
            an 'Err' if the deletion process enconters an issue.
        """
        try:
            x = await self.repository.delete_by_cid(cid=cid)
            return Ok(cid)
        except Exception as e:
            return Err(e)

    
    # async def create(self,observatory:)->Result[str,OcaError]:


class ObservatoriesService:
    """
    Service responsible for handling Observatory entities.
    Manages the lifecycle of observatories and their associations with level catalogs.
    """

    def __init__(self,
        repository:ObservatoriesRepository
    ):
        """Initializes the ObservatoriesService.
        
        Args:
            repository (ObservatoriesRepository): The data access layer for observatories.
        """
        self.repository = repository

    
    async def create(self,observatory:ObservatoryDTO)->Result[str,JubError]:
        """
        Creates a new observatory if one with the same ID does not already exist.

        This method enforces uniqueness on the 'obid'. It also assigns a default fallback
        image URL if the observatory is created without a specific graphical asset.

        Args:
            observatory (ObservatoryDTO): The data transfer object of the observatory.

        Returns:
            Result[str, JubError]: An 'Ok' with the new obid if creation succeds, or
            an 'Err' wrapping an AlreadyExists error if the obid is taken.
        """
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
        """
        Updates the hierarchical mapping of catalogs for a specific observatory.

        Args:
            obid (str): The unique identifier of the observatory.
            catalogs (List[LevelCatalogDTO]): The new list of level-catalog associations.

        Returns:
            Result[str,JubError]: An 'Ok' containing the obid if the update is successful,
            or an 'Err' if the database operation fails.
        """
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
        """
        Retrieves an observatory's full details by its unique identifier.

        Args:
            obid (str): The unique identifier of the observatory.

        Returns:
            Result[ObservatoryDTO, JubError]: An 'Ok' containing the ObservatoryDTO if found, 
            or an 'Err' wrapping a NotFound error if it does not exist.
        """

        try:
            x = await self.repository.find_by_obid(obid=obid)
            if x.is_none:
                return Err(NotFound(detail="Observatory not found."))
            
            return Ok(x.unwrap())

        except Exception as e:
            return Err(e)
        
    async def find_all(self,query:Dict[str,Any] = {}, skip:int =0, limit:int =0 )->List[ObservatoryDTO]:
        """
        Fetches a paginated list of observatories matching the provided query filters.

        Args:
            query (Dict[str, Any], optional): MongoDB filter criteria. Defaults to {}.
            skip (int, optional): Number of documents to skip for pagination. Defaults to 0.
            limit (int, optional): Maximum number of documents to return. Defaults to 0 (no limit).

        Returns:
            List[ObservatoryDTO]: A list of observatory data transfer objects.
        """
        return await self.repository.find_all(query=query,skip=skip,limit=limit)

    async def delete_by_obid(self, obid:str)->Result[str,JubError]:
        """
        Permanently removes an observatory from the database using its unique identifier.

        Args:
            obid (str): The unique identifier of the observatory to delete.
        """
        try:
            x = await self.repository.delete_by_obid(obid=obid)
            return Ok(obid)
        except Exception as e:
            return Err(e)

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
        """
        Performs a batch insertion of multiple products for bulk data loading.

        Args:
            products (List[ProductDTO], optional): A list of product DTOs to be inserted. Defaults to [].

        Returns:
            Result[List[str], JubError]: An 'Ok' containing a list of the inserted product PIDs, 
            or an 'Err' wrapping an error if the bulk insertion fails.
        """
        try:
            xs = list(map(lambda x : Product(**x.model_dump()), products))
            res = await self.repository.creates(products=xs)
            if res.is_err:
                return Err(UnknownError(detail="Products creation failed."))
            return Ok(list(map(lambda x :x.pid, products)))
        except Exception as e:
            return Err(e)
    async def find_by_pid(self, pid:str)->Result[ProductDTO, JubError]:
        """
        Retrieves a product's full details by its unique identifier.

        Args:
            pid (str): The unique identifier of the product.

        Returns:
            Result[ProductDTO, OcaError]: An 'Ok' containing the ProductDTO if found, 
            or an 'Err' wrapping a NotFound error if it does not exist.
        """
        try:
            xs = await self.repository.find_by_pid(pid=pid)
            if xs.is_none:
                return Err(NotFound(detail="Product not found."))
            return Ok(xs.unwrap())
        except Exception as e:
            return Err(UnknownError(detail=str(e)))
    
    async def find_all(self, query:Dict[str,Any]={}, skip:int =0, limit:int = 100)->Result[List[ProductDTO], JubError]:
        """
        Fetches a paginated list of products matching the provided query filters.

        Args:
            query (Dict[str, Any], optional): MongoDB filter criteria. Defaults to {}.
            skip (int, optional): Number of documents to skip for pagination. Defaults to 0.
            limit (int, optional): Maximum number of documents to return. Defaults to 100.

        Returns:
            Result[List[ProductDTO], OcaError]: An 'Ok' wrapping the list of matching products, 
            or an 'Err' if a database exception occurs.
        """
        try:
            xs = await self.repository.find_all(query=query, skip=skip,limit=limit)
            return Ok(xs)
        except Exception as e:
            return Err(UnknownError(detail=str(e)))
    async def find_all_by_ids(self, ids:List[ObjectId])->Result[List[ProductDTO],JubError]:
        """
        Retrieves multiple products by their internal MongoDB ObjectIds.

        Args:
            ids (List[ObjectId]): A list of internal MongoDB ObjectIds.

        Returns:
            Result[List[ProductDTO], JubError]: An 'Ok' wrapping the list of matching products, 
            or an 'Err' if a database exception occurs.
        """
        try:
            xs = await self.repository.find_all_by_ids(ids=ids)
            return Ok(xs)
        except Exception as e:
            return Err(UnknownError(detail=str(e)))
    async def filter_by_levels(self,tags:List[str],levels:List[str],skip:int=0, limit:int=100)->Result[List[ObjectId], JubError]:
        """
        Filters products strictly by matching tags and level inclusion.

        Args:
            tags (List[str]): List of keyword tags the products must contain.
            levels (List[str]): List of level identifiers the products must include.
            skip (int, optional): Number of documents to skip. Defaults to 0.
            limit (int, optional): Maximum number of documents to return. Defaults to 100.

        Returns:
            Result[List[ObjectId], JubError]: An 'Ok' wrapping the ObjectIds of the matched products, 
            or an 'Err' if the query execution fails.
        """
        try:
            xs = await self.repository.filter_by_levels(tags=tags,levels=levels, skip=skip, limit=limit)
            return Ok(xs)
        except Exception as e:
            return Err(UnknownError(detail=str(e)))

    async def delete_by_pid(self, pid:str)->Result[str, JubError]:
        """
        Permanently removes a product from the database using its ID.

        Args:
            pid (str): The unique identifier of the product to delete.

        Returns:
            Result[str, JubError]: An 'Ok' with the deleted pid if successful, 
            or an 'Err' if the deletion process encounters an issue.
        """
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
        """
        Dynamically filters products based on an observatory's context and multi-dimensional criteria.

        This constructs a MongoDB aggregation pipeline on the fly. It first 
        resolves the observatory to understand its temporal, spatial, and interest catalogs. 
        It then parses the incoming `ProductFilter` rules against these catalogs to build 
        specific `$match` rules (e.g., regex matching for spatial data, range checking for temporal data).

        Args:
            obid (str): The Observatory ID providing the catalog context for the filter.
            filters (ProductFilter): The complex filtering rules (tags, spatial, temporal, interest).
            skip (int, optional): Number of documents to skip. Defaults to 0.
            limit (int, optional): Maximum number of documents to return. Defaults to 100.

        Returns:
            List[ProductDTO]: A list of products that satisfy the dynamically constructed aggregation pipeline.

        Raises:
            Exception: Bubbles up any underlying OcaError if the target observatory or required catalogs cannot be found.
        """

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
