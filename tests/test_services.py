import pytest
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
import datetime as DT

import jubapi.repositories.v2 as RV4
import jubapi.models.v2 as MV4
import jubapi.services.v4 as SV4
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
        "db": db # Passed for direct assertions
    }

@pytest.mark.asyncio
async def test_full_observatory_workflow(services):
    """
    Tests the complete lifecycle: Observatory -> Catalogs -> Items/Hierarchy -> Products -> Retrieval.
    """
    catalog_service: SV4.CatalogService = services["catalog"]
    product_service: SV4.ProductService = services["product"]
    observatory_service: SV4.ObservatoryService = services["observatory"]
    obs = MV4.ObservatoryX(
            observatory_id="obs_breast_cancer", 
            title="Breast Cancer Observatory", 
            description="Experimental Observatory", 
            metadata={}
    )
    
    result = await observatory_service.create_observatory(obs)
    assert result.is_ok, f"Failed to create observatory: {result.unwrap_err()}"

    # A. SPATIAL Hierarchy (Root: spatial_root)
    result= await catalog_service.create_catalog(MV4.CatalogX(
            catalog_id    = "cat_country",
            root_group_id = "cat_spatial",
            name          = "Country",
            value         = "COUNTRY",
            catalog_type  = MV4.CatalogType.SPATIAL,
            level         = 0
        ))
    assert result.is_ok, f"Failed to create country catalog: {result.unwrap_err()}"

    result = await catalog_service.create_catalog(MV4.CatalogX(
        catalog_id    = "cat_state",
        root_group_id = "cat_spatial",
        name          = "State",
        value         = "STATE",
        catalog_type  = MV4.CatalogType.SPATIAL,
        level         = 1,
        parent_catalog_id = "cat_country"
    ))
    assert result.is_ok, f"Failed to create state catalog: {result.unwrap_err()}"

    result = await catalog_service.create_catalog(MV4.CatalogX(
        catalog_id    = "cat_mun",
        root_group_id = "cat_spatial",
        name          = "Municipality",
        value         = "MUNICIPALITY",
        catalog_type  = MV4.CatalogType.SPATIAL,
        level         = 2,
        parent_catalog_id = "cat_state"
    ))
    assert result.is_ok, f"Failed to create municipality catalog: {result.unwrap_err()}"

    # B. CIE10 Hierarchy (Root: cie10_root)
    result = await catalog_service.create_catalog(MV4.CatalogX(
        catalog_id    = "cat_chapter",
        root_group_id = "cat_cie10",
        name          = "Chapter",
        value         = "CHAPTER",
        catalog_type  = MV4.CatalogType.INTEREST,
        level         = 0
    ))
    assert result.is_ok, f"Failed to create chapter catalog: {result.unwrap_err()}"
    result = await catalog_service.create_catalog(MV4.CatalogX(
        catalog_id    = "cat_category",
        root_group_id = "cat_cie10",
        name          = "Category",
        value         = "CATEGORY",
        catalog_type  = MV4.CatalogType.INTEREST,
        level         = 1,
        parent_catalog_id = "cat_chapter"
    ))
    assert result.is_ok, f"Failed to create category catalog: {result.unwrap_err()}"

    # C. SEX (Flat, Root: sex_root)
    result = await catalog_service.create_catalog(MV4.CatalogX(
        catalog_id    = "cat_sex",
        root_group_id = "cat_sex",
        name          = "Sex",
        value         = "SEX",
        catalog_type  = MV4.CatalogType.INTEREST,
        level         = 0
    ))
    assert result.is_ok, f"Failed to create sex catalog: {result.unwrap_err()}"

    # D. TEMPORAL (Flat, Root: time_root)
    result = await catalog_service.create_catalog(MV4.CatalogX(
        catalog_id    = "cat_temporal",
        root_group_id = "cat_temporal",
        name          = "Temporal Variable",
        value         = "TEMPORAL",
        catalog_type  = MV4.CatalogType.TEMPORAL,
        level         = 0
    ))
    assert result.is_ok, f"Failed to create temporal catalog: {result.unwrap_err()}"
# SPATIAL: Mexico -> Tamaulipas -> Ciudad Victoria
    mx = MV4.CatalogItemX(catalog_item_id="MX", name="Mexico", value="MX", code=1, value_type=MV4.CatalogItemValueType.STRING, description="")
    tam = MV4.CatalogItemX(catalog_item_id="TAM", name="Tamaulipas", value="TAM", code=2, value_type=MV4.CatalogItemValueType.STRING, description="")
    
    slp = MV4.CatalogItemX(catalog_item_id="SLP", name="San Luis Potosi", value="SLP", code=3, value_type=MV4.CatalogItemValueType.STRING, description="")
    

    vic = MV4.CatalogItemX(catalog_item_id="VIC", name="Ciudad Victoria", value="VIC", code=3, value_type=MV4.CatalogItemValueType.STRING, description="")
    vic_aliases =[
        MV4.CatalogItemAlias(
            catalog_item_alias_id="CIUDAD_VICTORIA",
            value="CIUDAD_VICTORIA",
            value_type=MV4.CatalogItemValueType.STRING,
        ),
        MV4.CatalogItemAlias(
            catalog_item_alias_id="CD_VICTORIA",
            value="CD_VICTORIA",
            value_type=MV4.CatalogItemValueType.STRING,
        ),
        MV4.CatalogItemAlias(
            catalog_item_alias_id="VICTORIA",
            value="VICTORIA",
            value_type=MV4.CatalogItemValueType.STRING,
        )
    ]

    # victoria = MV4.CatalogItemX(catalog_item_id="VICTORIA", name="Ciudad Victoria", value="VIC", code=3, value_type=MV4.CatalogItemValueType.STRING, description="")
    # ciudad_victoria = MV4.CatalogItemX(catalog_item_id="CIUDAD_VICTORIA", name="Ciudad Victoria", value="VIC", code=3, value_type=MV4.CatalogItemValueType.STRING, description="")
    # cd_victoria = MV4.CatalogItemX(catalog_item_id="CD_VICTORIA", name="Ciudad Victoria", value="VIC", code=3, value_type=MV4.CatalogItemValueType.STRING, description="")
    
    r1 = await catalog_service.add_item_to_catalog("cat_country", mx)
    assert r1.is_ok, f"Failed to add Mexico to country catalog: {r1.unwrap_err()}"
    
    r2 = await catalog_service.add_item_to_catalog("cat_state", tam, parent_id="MX")
    assert r2.is_ok, f"Failed to add Tamaulipas to state catalog: {r2.unwrap_err()}"

    
    r3 = await catalog_service.add_item_to_catalog("cat_mun", vic, parent_id="TAM")
    assert r3.is_ok, f"Failed to add Ciudad Victoria to municipality catalog: {r3.unwrap_err()}"
    for alias in vic_aliases:
        r_alias = await catalog_service.add_value_to_item("VIC",  alias)
        assert r_alias.is_ok, f"Failed to add alias {alias.value} to Ciudad Victoria: {r_alias.unwrap_err()}"

    # CIE10: C (Neoplasms) -> C50 (Breast Cancer)
    c_chap = MV4.CatalogItemX(catalog_item_id="C", name="Chapter C: Neoplasms", value="C", code=1, value_type=MV4.CatalogItemValueType.STRING, description="")
    c_50 = MV4.CatalogItemX(catalog_item_id="C50", name="Breast Cancer", value="C50", code=2, value_type=MV4.CatalogItemValueType.STRING, description="")
    
    r4 = await catalog_service.add_item_to_catalog("cat_chapter", c_chap)
    assert r4.is_ok, f"Failed to add Chapter C Neoplasms to chapter catalog: {r4.unwrap_err()}"
    
    r5 = await catalog_service.add_item_to_catalog("cat_category", c_50, parent_id="C")
    assert r5.is_ok, f"Failed to add Breast Cancer to category catalog: {r5.unwrap_err()}"

    # SEX
    r6 = await catalog_service.add_item_to_catalog("cat_sex", MV4.CatalogItemX(catalog_item_id="MALE", name="Male", value="MALE", code=1, value_type=MV4.CatalogItemValueType.STRING, description=""))
    assert r6.is_ok, f"Failed to add Male to sex catalog: {r6.unwrap_err()}"
    r7 = await catalog_service.add_item_to_catalog("cat_sex", MV4.CatalogItemX(catalog_item_id="FEMALE", name="Female", value="FEMALE", code=2, value_type=MV4.CatalogItemValueType.STRING, description=""))
    assert r7.is_ok, f"Failed to add Female to sex catalog: {r7.unwrap_err()}"

    # TEMPORAL (Saved as ISO string padded to the start of the defined period)
    r8 = await catalog_service.add_item_to_catalog("cat_time", MV4.CatalogItemX(
        catalog_item_id="Y2023", name="2023", value="2023-01-01T00:00:00Z", code=2023, value_type=MV4.CatalogItemValueType.STRING, description=""
    ))
    assert r8.is_ok, f"Failed to add 2023 to time catalog: {r8.unwrap_err()}"
    r9 = await catalog_service.add_item_to_catalog("cat_time", MV4.CatalogItemX(
        catalog_item_id="Y2024", name="2024", value="2024", code=2024, value_type=MV4.CatalogItemValueType.STRING, description=""
    ))
    assert r9.is_ok, f"Failed to add 2024 to time catalog: {r9.unwrap_err()}"
    r10 = await catalog_service.add_item_to_catalog("cat_time", MV4.CatalogItemX(
        catalog_item_id="Y2025_05", name="May 2025", value="2025-05-01T00:00:00Z", code=2025, value_type=MV4.CatalogItemValueType.STRING, description=""
    ))
    assert r10.is_ok, f"Failed to add May 2025 to time catalog: {r10.unwrap_err()}"


    p1 = MV4.ProductX(product_id="prod_01", name="Clinical Cases Victoria 2024", description="", metadata={})
    await product_service.insert_product(p1, "obs_breast_cancer", ["FEMALE", "C50", "VIC", "Y2024"])

    # Product 2: Male Breast Cancer in Tamaulipas (State level), 2023
    p2 = MV4.ProductX(product_id="prod_02", name="Male Incidence TAM 2023", description="", metadata={})
    await product_service.insert_product(p2, "obs_breast_cancer", ["MALE", "C50", "TAM", "Y2023"])

    # Product 3: General Neoplasms (C) in Mexico (Country level), May 2025
    p3 = MV4.ProductX(product_id="prod_03", name="National Neoplasm Report May 2025", description="", metadata={})
    await product_service.insert_product(p3, "obs_breast_cancer", ["FEMALE", "C", "MX", "Y2025_05"])
    

    query_str = "jub.v1.VS(MX.TAM.*)"
    
    print(f"Query string: {query_str}")
    search_service = SV4.SearchService(
        observatory_product_link_repository        = observatory_service.graph_link_manager.observatory_product_link_repository,
        product_catalog_item_link_repository       = observatory_service.graph_link_manager.product_catalog_item_link_repository,
        catalog_item_relationship_repository       = observatory_service.graph_link_manager.catalog_item_relationship_repository,
        catalog_item_repository                    = catalog_service.catalog_item_repository,
        product_repository                         = product_service.product_repository,
        catalog_alias_repository                   = catalog_service.catalog_item_alias_repository,
        catalog_item_catalog_alias_link_repository = observatory_service.graph_link_manager.catalog_item_catalog_alias_link_repository
    )

    search_res = await search_service.execute_query(query_str, "obs_breast_cancer")
    assert search_res.is_ok, f"Search query failed: {search_res.unwrap_err()}"   
    # if search_res.is_err:
    #     print(f"Query failed: {search_res.unwrap_err()}")
    # else:
    #     products = search_res.unwrap()
    #     print(f"Query success! Found {len(products)} matching products:")
    #     for prod in products:
    #         print(f"   - [{prod.product_id}] {prod.name}")