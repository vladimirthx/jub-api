from jubapi.repositories.v4.base import BaseRepository
from motor.motor_asyncio import AsyncIOMotorCollection as Collection
from pymongo.results import UpdateResult,DeleteResult
import jubapi.models.v4 as MV4
from typing import List, Tuple
from option import Result,Err,Ok
import jubapi.errors as EX
from jubapi.log.log import Log
import os

log = Log(
    name = __name__,
    path = os.environ.get("JUB_LOG_PATH", "/log")
)


class ObservatoryRepository(BaseRepository[MV4.ObservatoryX]):
    def __init__(self, collection: Collection):
        super().__init__(collection, MV4.ObservatoryX, "observatory_id")

class ProductRepository(BaseRepository[MV4.ProductX]):
    def __init__(self, collection: Collection):
        super().__init__(collection, MV4.ProductX, "product_id")

class CatalogRepository(BaseRepository[MV4.CatalogX]):
    def __init__(self, collection: Collection):
        super().__init__(collection, MV4.CatalogX, "catalog_id")


class CatalogItemRepository(BaseRepository[MV4.CatalogItemX]):
    def __init__(self, collection: Collection):
        super().__init__(collection, MV4.CatalogItemX, "catalog_item_id")


class CatalogItemAliasRepository(BaseRepository[MV4.CatalogItemAlias]):
    def __init__(self, collection: Collection):
        super().__init__(collection, MV4.CatalogItemAlias, "catalog_item_alias_id")


# 1. Observatory <-> Product
class ObservatoryToProductLinkRepository(BaseRepository[MV4.ObservatoryToProductLink]):
    def __init__(self, collection: Collection):
        super().__init__(collection, MV4.ObservatoryToProductLink, "observatory_id")

# 2. Observatory <-> Catalog
class ObservatoryToCatalogLinkRepository(BaseRepository[MV4.ObservatoryToCatalogLink]):
    def __init__(self, collection: Collection):
        super().__init__(collection, MV4.ObservatoryToCatalogLink, "observatory_id")

# 3. Catalog -> Catalog Item
class CatalogToCatalogItemLinkRepository(BaseRepository[MV4.CatalogToCatalogItemLink]):
    def __init__(self, collection: Collection):
        super().__init__(collection, MV4.CatalogToCatalogItemLink, "catalog_id")

# 4. Product -> Catalog Item 
class ProductToCatalogItemLinkRepository(BaseRepository[MV4.CatalogItemToProductLink]):
    def __init__(self, collection: Collection):
        super().__init__(collection, MV4.CatalogItemToProductLink, "product_id")



# Catalog Item Value -> Catalog Item (The Alias Engine)
class CatalogItemToCatalogAliasLinkRepository(BaseRepository[MV4.CatalogItemToCatalogAliasLink]):
    def __init__(self, collection: Collection):
        super().__init__(collection, MV4.CatalogItemToCatalogAliasLink, "catalog_item_id")

# 5. Catalog Item -> Catalog Item (The Hierarchy Engine)
class CatalogItemRelationshipRepository(BaseRepository[MV4.CatalogItemRelationship]):
    def __init__(self, collection: Collection):
        super().__init__(collection, MV4.CatalogItemRelationship, "parent_id")

    
    async def get_all_children_nodes(self, root_parent_id: str,length:int = None) -> Result[List[str], EX.JubError]:
        """
        This hides the MongoDB $graphLookup logic.
        It resolves wildcards like MX.* by fetching the ID of every child node.
        """
        try: 
            pipeline = [
                {"$match": {"parent_id": root_parent_id}},
                {"$graphLookup": {
                    "from": self.collection.name,
                    "startWith": "$child_id",
                    "connectFromField": "child_id",
                    "connectToField": "parent_id",
                    "as": "descendants"
                }}
            ]
            
            cursor = self.collection.aggregate(pipeline) 
            results = await cursor.to_list(length=length)
            
            # Parse the results to return a simple list of child IDs
            descendant_ids = set()
            for doc in results:
                descendant_ids.add(doc["child_id"])
                for desc in doc.get("descendants", []):
                    descendant_ids.add(desc["child_id"])
                    
            return Ok(list(descendant_ids))
        except Exception as e:
            log.error(f"Error in get_all_children_nodes: {e}")
            return Err(EX.JubError.from_exception(e))



class GraphLinkManager:
    """
    Centralized manager for severing edges in the Jub graph.
    Relies strictly on injected Link Repositories.
    """
    def __init__(
        self, 
        observatory_product_link_repository: ObservatoryToProductLinkRepository,
        observatory_catalog_link_repository: ObservatoryToCatalogLinkRepository,
        catalog_catalog_item_link_repository: CatalogToCatalogItemLinkRepository,
        product_catalog_item_link_repository: ProductToCatalogItemLinkRepository,
        catalog_item_relationship_repository: CatalogItemRelationshipRepository,
        catalog_item_catalog_alias_link_repository: CatalogItemToCatalogAliasLinkRepository
    ):
        self.observatory_product_link_repository        = observatory_product_link_repository
        self.observatory_catalog_link_repository        = observatory_catalog_link_repository
        self.catalog_catalog_item_link_repository               = catalog_catalog_item_link_repository
        self.product_catalog_item_link_repository       = product_catalog_item_link_repository
        self.catalog_item_relationship_repository       = catalog_item_relationship_repository
        self.catalog_item_catalog_alias_link_repository = catalog_item_catalog_alias_link_repository

    # Get links
    async def get_products_linked_to_observatory(self, observatory_id: str) -> Result[List[str], EX.JubError]:
        try:
            cursor = self.observatory_product_link_repository.collection.find({"observatory_id": observatory_id})
            results = await cursor.to_list(length=None)
            product_ids = [doc["product_id"] for doc in results]
            return Ok(product_ids)
        except Exception as e:
            log.error(f"Error getting products linked to observatory: {e}")
            return Err(EX.JubError.from_exception(e))

    async def count_products_linked_to_observatory(self, observatory_id: str) -> Result[int, EX.JubError]:
        try:
            count = await self.observatory_product_link_repository.collection.count_documents({"observatory_id": observatory_id})
            return Ok(count)
        except Exception as e:
            log.error(f"Error counting products linked to observatory: {e}")
            return Err(EX.JubError.from_exception(e))
        
    async def exists_product_linked_to_observatory(self, observatory_id: str, product_id:str) -> Result[bool, EX.JubError]:
        try:
            count = await self.observatory_product_link_repository.collection.count_documents({"observatory_id": observatory_id, "product_id": product_id})
            return Ok(count > 0)
        except Exception as e:
            log.error(f"Error checking existence of product linked to observatory: {e}")
            return Err(EX.JubError.from_exception(e))
        
    async def exists_products_linked_to_observatory(self, observatory_id: str) -> Result[bool, EX.JubError]:
        try:
            count = await self.observatory_product_link_repository.collection.count_documents({"observatory_id": observatory_id})
            return Ok(count > 0)
        except Exception as e:
            log.error(f"Error checking existence of products linked to observatory: {e}")
            return Err(EX.JubError.from_exception(e))
    
    # _______________________
    async def get_catalogs_linked_to_observatory(self, observatory_id: str) -> Result[List[str], EX.JubError]:
        try:
            cursor = self.observatory_catalog_link_repository.collection.find({"observatory_id": observatory_id})
            results = await cursor.to_list(length=None)
            catalog_ids = [doc["catalog_id"] for doc in results]
            return Ok(catalog_ids)
        except Exception as e:
            log.error(f"Error getting catalogs linked to observatory: {e}")
            return Err(EX.JubError.from_exception(e))
    async def count_catalogs_linked_to_observatory(self, observatory_id: str) -> Result[int, EX.JubError]:
        try:
            count = await self.observatory_catalog_link_repository.collection.count_documents({"observatory_id": observatory_id})
            return Ok(count)
        except Exception as e:
            log.error(f"Error counting catalogs linked to observatory: {e}")
            return Err(EX.JubError.from_exception(e))
    async def exists_catalog_linked_to_observatory(self, observatory_id: str, catalog_id:str) -> Result[bool, EX.JubError]:
        try:
            count = await self.observatory_catalog_link_repository.collection.count_documents({"observatory_id": observatory_id, "catalog_id": catalog_id})
            return Ok(count > 0)
        except Exception as e:
            log.error(f"Error checking existence of catalog linked to observatory: {e}")
            return Err(EX.JubError.from_exception(e))
    async def exists_catalogs_linked_to_observatory(self, observatory_id: str) -> Result[bool, EX.JubError]:
        try:
            count = await self.observatory_catalog_link_repository.collection.count_documents({"observatory_id": observatory_id})
            return Ok(count > 0)
        except Exception as e:
            log.error(f"Error checking existence of catalogs linked to observatory: {e}")
            return Err(EX.JubError.from_exception(e))
    # _______________________
    async def get_catalog_items_linked_to_catalog(self, catalog_id: str) -> Result[List[str], EX.JubError]:
        try:
            cursor = self.catalog_catalog_item_link_repository.collection.find({"catalog_id": catalog_id})
            results = await cursor.to_list(length=None)
            catalog_item_ids = [doc["catalog_item_id"] for doc in results]
            return Ok(catalog_item_ids)
        except Exception as e:
            log.error(f"Error getting catalog items linked to catalog: {e}")
            return Err(EX.JubError.from_exception(e))
    async def count_catalog_items_linked_to_catalog(self, catalog_id: str) -> Result[int, EX.JubError]:
        try:
            count = await self.catalog_catalog_item_link_repository.collection.count_documents({"catalog_id": catalog_id})
            return Ok(count)
        except Exception as e:
            log.error(f"Error counting catalog items linked to catalog: {e}")
            return Err(EX.JubError.from_exception(e))
    async def exists_catalog_item_linked_to_catalog(self, catalog_id: str, catalog_item_id:str) -> Result[bool, EX.JubError]:
        try:
            count = await self.catalog_catalog_item_link_repository.collection.count_documents({"catalog_id": catalog_id, "catalog_item_id": catalog_item_id})
            return Ok(count > 0)
        except Exception as e:
            log.error(f"Error checking existence of catalog item linked to catalog: {e}")
            return Err(EX.JubError.from_exception(e))
    async def exists_catalog_items_linked_to_catalog(self, catalog_id: str) -> Result[bool, EX.JubError]:
        try:
            count = await self.catalog_catalog_item_link_repository.collection.count_documents({"catalog_id": catalog_id})
            return Ok(count > 0)
        except Exception as e:
            log.error(f"Error checking existence of catalog items linked to catalog: {e}")
            return Err(EX.JubError.from_exception(e))
    # _______________________
    async def get_catalog_items_linked_to_product(self, product_id: str) -> Result[List[str], EX.JubError]:
        try:
            cursor = self.product_catalog_item_link_repository.collection.find({"product_id": product_id})
            results = await cursor.to_list(length=None)
            catalog_item_ids = [doc["catalog_item_id"] for doc in results]
            return Ok(catalog_item_ids)
        except Exception as e:
            log.error(f"Error getting catalog items linked to product: {e}")
            return Err(EX.JubError.from_exception(e))
    async def count_catalog_items_linked_to_product(self, product_id: str) -> Result[int, EX.JubError]:
        try:
            count = await self.product_catalog_item_link_repository.collection.count_documents({"product_id": product_id})
            return Ok(count)
        except Exception as e:
            log.error(f"Error counting catalog items linked to product: {e}")
            return Err(EX.JubError.from_exception(e))
    async def exists_catalog_item_linked_to_product(self, product_id: str, catalog_item_id:str) -> Result[bool, EX.JubError]:
        try:
            count = await self.product_catalog_item_link_repository.collection.count_documents({"product_id": product_id, "catalog_item_id": catalog_item_id})
            return Ok(count > 0)
        except Exception as e:
            log.error(f"Error checking existence of catalog item linked to product: {e}")
            return Err(EX.JubError.from_exception(e))
    async def exists_catalog_items_linked_to_product(self, product_id: str) -> Result[bool, EX.JubError]:
        try:
            count = await self.product_catalog_item_link_repository.collection.count_documents({"product_id": product_id})
            return Ok(count > 0)
        except Exception as e:
            log.error(f"Error checking existence of catalog items linked to product: {e}")
            return Err(EX.JubError.from_exception(e))
    # _______________________


    async def link_observatory_to_product(self, observatory_id: str, product_id: str)->Result[UpdateResult,EX.JubError]:
        try:
            link = MV4.ObservatoryToProductLink(observatory_id=observatory_id, product_id=product_id)
            r = await self.observatory_product_link_repository.collection.update_one(
                {"observatory_id": observatory_id, "product_id": product_id},
                {"$set": link.model_dump()},
                upsert=True
            )
            return Ok(r)
        except Exception as e:
            log.error(f"Error linking observatory to product: {e}")
            return Err(EX.JubError.from_exception(e))
            # raise EX.JubError(f"Failed to link observatory to product: {str(e)}")

    async def link_observatory_to_catalog(self, observatory_id: str, catalog_id: str,level:int=0)->Result[UpdateResult,EX.JubError]:
        try:
            link = MV4.ObservatoryToCatalogLink(observatory_id=observatory_id, catalog_id=catalog_id,level=level)
            r = await self.observatory_catalog_link_repository.collection.update_one(
                {"observatory_id": observatory_id, "catalog_id": catalog_id},
                {"$set": link.model_dump()},
                upsert=True
            )
            return Ok(r)
        except Exception as e:
            log.error(f"Error linking observatory to catalog: {e}")
            return Err(EX.JubError.from_exception(e))
        

    async def link_catalog_to_item(self, catalog_id: str, catalog_item_id: str)->Result[UpdateResult,EX.JubError]:
        try:
            link = MV4.CatalogToCatalogItemLink(catalog_id=catalog_id, catalog_item_id=catalog_item_id)
            r = await self.catalog_catalog_item_link_repository.collection.update_one(
                {"catalog_id": catalog_id, "catalog_item_id": catalog_item_id},
                {"$set": link.model_dump()},
                upsert=True
            )
            return Ok(r)
        except Exception as e:
            log.error(f"Error linking catalog to item: {e}")
            return Err(EX.JubError.from_exception(e))
        

    async def link_product_to_catalog_item(self, product_id: str, catalog_item_id: str)->Result[UpdateResult,EX.JubError]:
        """Tags a product with a specific dimension (e.g., 'FEMALE' or 'VIC')."""
        try:
            link = MV4.CatalogItemToProductLink(product_id=product_id, catalog_item_id=catalog_item_id)
            r = await self.product_catalog_item_link_repository.collection.update_one(
                {"product_id": product_id, "catalog_item_id": catalog_item_id},
                {"$set": link.model_dump()},
                upsert=True
            )
            return Ok(r)
        except Exception as e:
            log.error(f"Error linking product to catalog item: {e}")
            return Err(EX.JubError.from_exception(e))
        

    async def set_item_relationship(self, parent_id: str, child_id: str)->Result[UpdateResult,EX.JubError]:
        """Builds the hierarchy (e.g., MX -> TAM)."""
        try:
            link = MV4.CatalogItemRelationship(parent_id=parent_id, child_id=child_id)
            r = await self.catalog_item_relationship_repository.collection.update_one(
                {"parent_id": parent_id, "child_id": child_id},
                {"$set": link.model_dump()},
                upsert=True
            )
            return Ok(r)
        except Exception as e:
            log.error(f"Error setting item relationship: {e}")
            return Err(EX.JubError.from_exception(e))

    async def link_item_to_alias(self, catalog_item_id: str, catalog_item_alias_id: str)->Result[UpdateResult,EX.JubError]:
        """Links an alias/value to the canonical item."""
        try:

            link = MV4.CatalogItemToCatalogAliasLink(
                catalog_item_id=catalog_item_id, 
                catalog_item_alias_id=catalog_item_alias_id
            )
            r = await self.catalog_item_catalog_alias_link_repository.collection.update_one(
                {"catalog_item_id": catalog_item_id, "catalog_item_value_id": catalog_item_alias_id},
                {"$set": link.model_dump()},
                upsert=True
            )
            return Ok(r)
        except Exception as e:
            log.error(f"Error linking item to value: {e}")
            return Err(EX.JubError.from_exception(e))

    #  Remove links (called by services when an entity is deleted, to maintain graph integrity)
    async def remove_all_product_links(self, product_id: str)->Result[Tuple[DeleteResult, DeleteResult],EX.JubError]:
        """Called by ProductService when a product is completely deleted."""
        try:
            r1 = await self.observatory_product_link_repository.collection.delete_many({"product_id": product_id})
            r2 = await self.product_catalog_item_link_repository.collection.delete_many({"product_id": product_id})
            return Ok((r1, r2))
        except Exception as e:
            log.error(f"Error removing all product links: {e}")
            return Err(EX.JubError.from_exception(e))


    async def remove_all_catalog_links(self, catalog_id: str)->Result[Tuple[DeleteResult, DeleteResult],EX.JubError]:
        """Called by CatalogService when a catalog is completely deleted."""
        try:
            r1 = await self.observatory_catalog_link_repository.collection.delete_many({"catalog_id": catalog_id})
            r2 = await self.catalog_catalog_item_link_repository.collection.delete_many({"catalog_id": catalog_id})
            return Ok((r1, r2))
        except Exception as e:
            log.error(f"Error removing all catalog links: {e}")
            return Err(EX.JubError.from_exception(e))

    async def remove_all_catalog_item_links(self, catalog_item_id: str)->Result[Tuple[DeleteResult, DeleteResult, DeleteResult, DeleteResult],EX.JubError]:
        """
        Called by CatalogService when an item is deleted. 
        Wipes its tags, its aliases, and its parent/child relationships.
        """
        try:
            r1 = await self.catalog_catalog_item_link_repository.collection.delete_many({"catalog_item_id": catalog_item_id})
            r2 = await self.product_catalog_item_link_repository.collection.delete_many({"catalog_item_id": catalog_item_id})
            r3 = await self.catalog_item_catalog_alias_link_repository.collection.delete_many({"catalog_item_id": catalog_item_id})
            
            # Remove it from the hierarchy tree (whether it was a parent or a child)
            r4 = await self.catalog_item_relationship_repository.collection.delete_many({"$or": [
                {"parent_id": catalog_item_id},
                {"child_id": catalog_item_id}
            ]})
            return Ok((r1, r2, r3, r4))
        except Exception as e:
            log.error(f"Error removing all catalog item links: {e}")
            return Err(EX.JubError.from_exception(e))

    