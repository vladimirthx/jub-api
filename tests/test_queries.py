import pytest
import asyncio
from jubapi.querylang.v2.parser import QueryAST
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
import datetime as DT

import jubapi.repositories.v2 as RV4
import jubapi.models.v2 as MV4
import jubapi.services.v2 as SV4
from jubapi.db import CollectionNames


@pytest.fixture(scope="function")
async def db():
    """Provides a clean test database."""
    client = MongoClient("mongodb://localhost:27027/")
    db = client.jub_test
    yield db
    await client.drop_database('jub_test')

@pytest.fixture(scope="function")
async def services(db):
    """Initializes all required repositories and services."""
    # 1. Repositories
    observatory_repository        = RV4.ObservatoryRepository(db[CollectionNames.OBSERVATORIES.value])
    product_repository            = RV4.ProductRepository(db[CollectionNames.PRODUCTS.value])
    catalog_repository            = RV4.CatalogRepository(db[CollectionNames.CATALOGS.value])
    catalog_item_repository       = RV4.CatalogItemRepository(db[CollectionNames.CATALOG_ITEMS.value])
    catalog_item_value_repository = RV4.CatalogItemAliasRepository(db[CollectionNames.CATALOG_ITEM_VALUES.value])
    
    # 2. Link Manager
    link_manager = RV4.GraphLinkManager(
        observatory_product_link_repository        = RV4.ObservatoryToProductLinkRepository(db[CollectionNames.OBSERVATORY_PRODUCT_LINKS.value]),
        product_catalog_item_link_repository       = RV4.ProductToCatalogItemLinkRepository(db[CollectionNames.PRODUCT_CATALOGS_ITEM_LINKS.value]),
        catalog_item_relationship_repository       = RV4.CatalogItemRelationshipRepository(db[CollectionNames.CATALOG_ITEM_RELATIONSHIPS.value]),
        catalog_catalog_item_link_repository       = RV4.CatalogToCatalogItemLinkRepository(db[CollectionNames.CATALOG_CATALOG_ITEM_LINKS.value]),
        catalog_item_catalog_alias_link_repository = RV4.CatalogItemToCatalogAliasLinkRepository(db[CollectionNames.CATALOG_ITEM_CATALOG_ALIAS_LINKS.value]),
        observatory_catalog_link_repository        = RV4.ObservatoryToCatalogLinkRepository(db[CollectionNames.OBSERVATORY_CATALOG_LINKS.value])
    )
    search_service = SV4.SearchService(
        observatory_product_link_repository        = link_manager.observatory_product_link_repository,
        product_catalog_item_link_repository       = link_manager.product_catalog_item_link_repository,
        catalog_item_relationship_repository       = link_manager.catalog_item_relationship_repository,
        catalog_item_repository                    = catalog_item_repository,
        product_repository                         = product_repository,
        catalog_alias_repository                   = catalog_item_value_repository,
        catalog_item_catalog_alias_link_repository = link_manager.catalog_item_catalog_alias_link_repository
    )

    # 3. Services
    return {
        "catalog": SV4.CatalogService(catalog_repository, catalog_item_repository, catalog_item_value_repository, link_manager),
        "product": SV4.ProductService(product_repository, link_manager),
        "observatory": SV4.ObservatoryService(
            observatory_product_link_repository = link_manager.observatory_product_link_repository,
            observatory_repository              = observatory_repository,
            product_repository                  = product_repository,
            graph_link_manager                  = link_manager
        ),
        "search": search_service,
        "db": db # Passed for direct assertions
    }


@pytest.fixture(autouse=True)
async def seed_database(services):
    """Seeds the database before the tests run."""
    cat_srv:SV4.CatalogService = services["catalog"]
    prod_srv: SV4.ProductService = services["product"]
    observatory_srv: SV4.ObservatoryService = services["observatory"]
    
    # 1. Seed Temporal Catalog Items (The key to making time work in the graph)
    # The 'value' field must be a sortable string (like ISO dates or year strings)
    # so the math operators (>, <, >=) work natively in MongoDB.
    # await services[""]
    await observatory_srv.add_catalog("obs_test", "cat_spatial", 0)
    await observatory_srv.add_catalog("obs_test", "cat_time", 1)

    await cat_srv.add_item_to_catalog("cat_time", MV4.CatalogItemX(
        catalog_item_id = "Y2020",
        name            = "2020",
        value           = "2020",
        code            = 2020,
        temporal_value  = "2020-01-01T00:00:00Z",
        value_type      = MV4.CatalogItemValueType.DATETIME,
        description     = ""
    ))
    await cat_srv.add_item_to_catalog(
        "cat_time", 
        MV4.CatalogItemX(
            catalog_item_id = "Y2023",
            name            = "2023",
            value           = "2023",
            temporal_value  = "2023-01-01T00:00:00Z",
            code            = 2023,
            value_type      = MV4.CatalogItemValueType.DATETIME,
            description     = ""
        )
    )
    await cat_srv.add_item_to_catalog(
        "cat_time", 
        MV4.CatalogItemX(
            catalog_item_id = "Y2024",
            name            = "2024",
            value           = "2024",
            temporal_value  = "2024-01-01T00:00:00Z",
            code            = 2024,
            value_type      = MV4.CatalogItemValueType.DATETIME,
            description     = ""
        )
    )
    await cat_srv.add_item_to_catalog(
        "cat_time", 
        MV4.CatalogItemX(
            catalog_item_id = "Y2025",
            name            = "2025",
            value           = "2025",
            temporal_value  = "2025-01-01T00:00:00Z",
            code            = 2025,
            value_type      = MV4.CatalogItemValueType.DATETIME,
            description     = ""
        )
    )

    # 2. Seed Spatial & Interest Items (Simplified for tests)
    await cat_srv.add_item_to_catalog("cat_spatial", MV4.CatalogItemX(catalog_item_id="TAM", name="Tamaulipas", value="TAM", code=1, value_type="STRING", description=""))
    await cat_srv.add_item_to_catalog("cat_spatial", MV4.CatalogItemX(catalog_item_id="VIC", name="Victoria", value="VIC", code=2, value_type="STRING", description=""), parent_id="TAM")
    await cat_srv.add_item_to_catalog("cat_spatial", MV4.CatalogItemX(catalog_item_id="SLP", name="San Luis Potosi", value="SLP", code=3, value_type="STRING", description=""))
    
    await cat_srv.add_item_to_catalog("cat_sex", MV4.CatalogItemX(catalog_item_id="FEMALE", name="Female", value="FEMALE", code=1, value_type="STRING", description=""))
    await cat_srv.add_item_to_catalog("cat_sex", MV4.CatalogItemX(catalog_item_id="MALE", name="Male", value="MALE", code=2, value_type="STRING", description=""))

    # 3. Seed Products
    # Product 1: Victoria, Female, 2024
    await prod_srv.insert_product(MV4.ProductX(product_id="p1", name="VIC_FEM_2024", description=""), "obs_test", ["VIC", "FEMALE", "Y2024"])
    
    # Product 2: Tamaulipas (State), Male, 2023
    await prod_srv.insert_product(MV4.ProductX(product_id="p2", name="TAM_MALE_2023", description=""), "obs_test", ["TAM", "MALE", "Y2023"])
    
    # Product 3: Disjointed Dates! SLP, Female, covers both 2020 AND 2025
    await prod_srv.insert_product(MV4.ProductX(product_id="p3", name="SLP_FEM_MULTI_DATE", description=""), "obs_test", ["SLP", "FEMALE", "Y2020", "Y2025"])


@pytest.mark.asyncio
async def test_vs_spatial_hierarchy(services):
    search_srv:SV4.SearchService = services["search"]
    
    # Query: Anything inside Tamaulipas
    res = await search_srv.execute_query("jub.v1.VS(TAM.*)", "obs_test")
    
    assert res.is_ok
    products = [p.product_id for p in res.unwrap()]
    
    # Should find p1 (VIC is inside TAM) and p2 (Tagged directly with TAM)
    assert "p1" in products
    assert "p2" in products
    assert "p3" not in products # SLP is not inside TAM

@pytest.mark.asyncio
async def test_vt_exact_time(services):
    search_srv: SV4.SearchService = services["search"]
    
    # Query: Exactly 2024
    res = await search_srv.execute_query("jub.v1.VT(2024)", "obs_test")
    
    assert res.is_ok
    products = [p.product_id for p in res.unwrap()]
    assert "p1" in products # p1 is 2024
    assert "p2" not in products
    assert "p3" not in products

@pytest.mark.asyncio
async def test_vt_math_operator_greater_than(services):
    search_srv = services["search"]
    
    # Query: Any time strictly greater than 2023
    # The code maps '>' to '$gt' and searches the CatalogItem 'value' field.
    # It will find IDs ['Y2024', 'Y2025'].
    res = await search_srv.execute_query("jub.v1.VT(> 2023)", "obs_test")
    
    assert res.is_ok
    products = [p.product_id for p in res.unwrap()]
    assert "p1" in products # p1 has Y2024
    assert "p3" in products # p3 has Y2025
    assert "p2" not in products # p2 is exactly 2023 (not >)

@pytest.mark.asyncio
async def test_vt_multi_date_product(services):
    search_srv = services["search"]
    
    # Query: Exactly 2020
    # Proves we can find products that have disjointed dates
    res = await search_srv.execute_query("jub.v1.VT(2020)", "obs_test")
    
    assert res.is_ok
    products = [p.product_id for p in res.unwrap()]
    assert products == ["p3"] # p3 is tagged with both Y2020 and Y2025

@pytest.mark.asyncio
async def test_vt_math_operator_range(services):
    search_srv:SV4.SearchService = services["search"]
    
    # Query: Time between 2021 and 2024 inclusive
    res = await search_srv.execute_query("jub.v1.VT(>= 2021 AND <= 2024)", "obs_test")
    
    assert res.is_ok
    products = [p.product_id for p in res.unwrap()]
    print(f"Products found in range query: {products}")
    assert "p1" in products # 2024
    assert "p2" in products # 2023
    assert "p3" not in products # 2020 is too early, 2025 is too late

@pytest.mark.asyncio
async def test_complex_combination(services):
    search_srv = services["search"]
    
    # Query: Female AND (inside Tamaulipas) AND (after 2023)
    query_str = "jub.v1.VS(TAM.*).VI(FEMALE).VT(> 2023)"
    res = await search_srv.execute_query(query_str, "obs_test")
    
    assert res.is_ok
    products = [p.product_id for p in res.unwrap()]
    
    # Only p1 matches all three conditions
    assert len(products) == 1
    assert "p1" in products