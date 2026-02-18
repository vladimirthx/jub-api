import pytest
from jubapi.db import get_collection,connect_to_mongo,close_mongo_connection
from jubapi.repositories.v3 import XVariableRepository,CatalogRelationshipRepository,CatalogRepository,CatalogXVariableRepository,MetaCatalogCatalogRepository,MetaCatalogRepository,XVariableParentRepository
from jubapi.services.v3 import XVariableService,CatalogRelationshipService,CatalogService,CatalogXVariableService,MetaCatalogCatalogService,MetaCatalogService,XVariableParentService
from jubapi.models.v3 import XVariable,XTypeEnum,VariableTypeEnum



@pytest.fixture
async def xvar_service():
    """Fixture to setup the Catalog service and repository."""
    c          = get_collection(name="xvars")
    repository = XVariableRepository(collection=c)
    service    = XVariableService(repository=repository)
    # Return repository and service for use in tests
    return repository, service
@pytest.fixture
def metadata_catalog_catalog_service()->MetaCatalogCatalogService:
    collection =  get_collection(name="meta_catalog_catalog")
    repository = MetaCatalogCatalogRepository(collection= collection)
    service = MetaCatalogCatalogService(repository= repository)
    return repository, service

@pytest.fixture
def metadata_catalog_service()->MetaCatalogService:
    collection =  get_collection(name="meta_catalog")
    repository = MetaCatalogRepository(collection= collection)
    service = MetaCatalogService(repository= repository)
    return repository, service

@pytest.fixture
def catalog_service()->CatalogService:
    collection =  get_collection(name="catalog")
    repository = CatalogRepository(collection= collection)
    service = CatalogService(repository= repository)
    return repository, service

@pytest.fixture
def catalog_xvar_service()->CatalogXVariableService:
    collection =  get_collection(name="catalog_xvar")
    repository = CatalogXVariableRepository(collection= collection)
    service = CatalogXVariableService(repository= repository)
    return repository, service
@pytest.fixture
def catalog_relatioshiop_service()->CatalogRelationshipService:
    collection =  get_collection(name="catalog_relatioship")
    repository = CatalogRelationshipRepository(collection= collection)
    service = CatalogRelationshipService(repository= repository)
    return repository, service
@pytest.fixture
def xvar_parent_service()->XVariableParentService:
    collection =  get_collection(name="xvar_parent")
    repository = XVariableParentRepository(collection= collection)
    service = XVariableParentService(repository= repository)
    return repository, service


@pytest.mark.asyncio
async def test_reset_collections(
    xvar_service,
    metadata_catalog_catalog_service,
    metadata_catalog_service,
    catalog_service,
    catalog_xvar_service,
    catalog_relatioshiop_service,
    xvar_parent_service
):
    repo1,service1 = metadata_catalog_catalog_service
    repo2,service2 = metadata_catalog_service
    repo3,service3 = catalog_service
    repo4,service4 = xvar_service
    repo5,service5 = catalog_xvar_service
    repo6,service6 = catalog_relatioshiop_service 
    repo7,service7 = xvar_parent_service

    

    


    # model = XVariable(xtype=XTypeEnum.SPATIAL,value="Mexico", variable_type=VariableTypeEnum.STRING)
    # res   = await repo.create(data=model.model_dump())
    # res1  = await service.create(model=model)
    # print(model,res)
    # service.create(model= model)
