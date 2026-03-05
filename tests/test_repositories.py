import pytest
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient
import jubapi.repositories.v2 as RV4
import jubapi.models.v2 as MV4
from jubapi.db import CollectionNames

@pytest.fixture(scope="function")
async def test_db():
    """
    Sets up a clean MongoDB test database before tests run,
    and drops it completely after all tests in this module finish.
    """
    client = MongoClient("mongodb://localhost:27027/")
    db = client.jub_test_database
    
    # Yield the db to the tests
    yield db
    
    # Teardown: Clean up after tests are done
    client.drop_database('jub_test_database')

@pytest.fixture
def repos(test_db):
    """Provides initialized repositories for the tests."""
    
    obs_prod_links_repo = RV4.ObservatoryToProductLinkRepository(test_db[CollectionNames.OBSERVATORY_PRODUCT_LINKS.value])
    obs_cat_links_repo = RV4.ObservatoryToCatalogLinkRepository(test_db[CollectionNames.OBSERVATORY_CATALOG_LINKS.value])
    cat_item_links_repo = RV4.CatalogToCatalogItemLinkRepository(test_db[CollectionNames.CATALOG_CATALOG_ITEM_LINKS.value])
    prod_cat_item_links_repo = RV4.ProductToCatalogItemLinkRepository(test_db[CollectionNames.PRODUCT_CATALOGS_ITEM_LINKS.value])
    cat_item_rels_repo = RV4.CatalogItemRelationshipRepository(test_db[CollectionNames.CATALOG_ITEM_RELATIONSHIPS.value])
    cat_item_val_links_repo = RV4.CatalogItemToCatalogAliasLinkRepository(test_db[CollectionNames.CATALOG_ITEM_CATALOG_ALIAS_LINKS.value])

    return {
        "obs": RV4.ObservatoryRepository(test_db[CollectionNames.OBSERVATORIES.value]),
        "prod": RV4.ProductRepository(test_db[CollectionNames.PRODUCTS.value]),
        "cat": RV4.CatalogRepository(test_db[CollectionNames.CATALOGS.value]),
        "item": RV4.CatalogItemRepository(test_db[CollectionNames.CATALOG_ITEMS.value]),
        "links": RV4.GraphLinkManager(
            obs_prod_links_repo,
            obs_cat_links_repo,
            cat_item_links_repo,
            prod_cat_item_links_repo,
            cat_item_rels_repo,
            cat_item_val_links_repo
       
        ),
        "db": test_db # Pass the raw db just to check link collections directly
    }

@pytest.mark.asyncio
async def test_repository_crud_operations(repos):
    """
    Test that the BaseRepository correctly inserts, fetches, and deletes.
    """
    prod_repo:RV4.ProductRepository = repos["prod"]
    
    # 1. Insert
    pid1 = "prod_test_01"
    new_prod = MV4.ProductX(
        product_id  = pid1,
        name        = "Test Breast Cancer Report",
        description = "A test description",
        metadata    = {"year": "2024"}
    )
    inserted_id_result = await prod_repo.insert(new_prod)
    assert inserted_id_result.is_ok
    inserted_id =inserted_id_result.unwrap()

    assert inserted_id == pid1
    
    # 2. Fetch
    fetched_prod_result = await prod_repo.get_by_id(pid1)
    assert fetched_prod_result.is_ok
    fetched_prod = fetched_prod_result.unwrap()
    assert fetched_prod is not None
    assert fetched_prod.name == "Test Breast Cancer Report"
    assert fetched_prod.metadata["year"] == "2024"
    
    # 3. Find Many
    results_result = await prod_repo.find_many({"product_id": pid1})
    assert results_result.is_ok
    results = results_result.unwrap()
    assert len(results) == 1
    
    # 4. Delete
    deleted = await prod_repo.delete(pid1)
    assert deleted.is_ok
    assert (await prod_repo.get_by_id(pid1)).is_err

@pytest.mark.asyncio
async def test_graph_link_manager(repos):
    """
    Test that the GraphLinkManager properly connects entities.
    """
    # 1. Setup entities
    obs_id = "obs_test_01"
    prod_id = "prod_test_02"
    cat_id = "cat_spatial_01"
    item_id = "item_mx_01"
    
    observatory_repository:RV4.ObservatoryRepository = repos["obs"]
    product_repository    :RV4.ProductRepository     = repos["prod"]
    catalog_repository    :RV4.CatalogRepository     = repos["cat"]
    graph_linker_manager  :RV4.GraphLinkManager      = repos["links"]

    result = await observatory_repository.insert(MV4.ObservatoryX(observatory_id=obs_id, title="Test Obs", description="", metadata={}))
    assert result.is_ok, f"Failed to insert observatory: {result.unwrap_err()}"
    
    result = await product_repository.insert(MV4.ProductX(product_id=prod_id, name="Test Prod", description="", metadata={}))
    assert result.is_ok, f"Failed to insert product: {result.unwrap_err()}"
    
    # 2. Test Observatory -> Product Link
    result = await graph_linker_manager.link_observatory_to_product(obs_id, prod_id)
    assert result.is_ok, f"Failed to link observatory to product: {result.unwrap_err()}"
    
    # Verify the link was created directly in the mongo collection
    link_doc = await graph_linker_manager.observatory_product_link_repository.collection.find_one({"observatory_id": obs_id, "product_id": prod_id})
    assert link_doc is not None
    assert link_doc["observatory_id"] == obs_id
    
    # 3. Test Product -> Catalog Item Link (Tagging)
    result = await graph_linker_manager.link_product_to_catalog_item(prod_id, item_id)
    assert result.is_ok, f"Failed to link product to catalog item: {result.unwrap_err()}"
    
    # tag_doc = await graph_linker_manager.product_catalog_item_link_repository.collection.find_one({"product_id": prod_id, "catalog_item_id": item_id})
    tag_doc_results = await graph_linker_manager.get_catalog_items_linked_to_product(product_id=prod_id)
    assert tag_doc_results.is_ok, f"Failed to get catalog items linked to product: {tag_doc_results.unwrap_err()}"
    tags_doc = tag_doc_results.unwrap()
    print("TAGS DOCS:", tags_doc)
    assert item_id in tags_doc
  

@pytest.mark.asyncio
async def test_catalog_hierarchy_links(repos):
    """
    Test the self-referential parent/child links for catalog items.
    """
    parent_id = "item_mx"
    child_id = "item_slp"
    
    await repos["links"].set_item_relationship(parent_id, child_id)
    
    rel_doc = await repos["db"].catalog_item_relationships.find_one({"parent_id": parent_id, "child_id": child_id})
    assert rel_doc is not None
    assert rel_doc["child_id"] == "item_slp"