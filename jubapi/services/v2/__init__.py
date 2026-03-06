from os import path
from typing import List,Optional
import jubapi.models.v2 as MV4
import jubapi.repositories.v2 as RV4
from jubapi.querylang.v2.parser  import QueryAST,Condition,ConditionOperators
import jubapi.errors as EX
from option import Result,Ok,Err
from jubapi.log.log import Log
import os
from jubapi.db import CollectionNames
import datetime as DT

log = Log(
    name = __name__,
    path = os.environ.get("JUB_LOG_PATH", "/log"),
)

class ObservatoryService:
    def __init__(
        self, 
        observatory_repository: RV4.ObservatoryRepository, 
        observatory_product_link_repository: RV4.ObservatoryToProductLinkRepository,
        product_repository: RV4.ProductRepository,
        graph_link_manager: RV4.GraphLinkManager
    ):
        self.observatory_repository = observatory_repository
        self.observatory_product_link_repository = observatory_product_link_repository
        self.product_repository = product_repository
        self.graph_link_manager = graph_link_manager

    # --- Create Operations ---

    async def create_observatory(self, observatory: MV4.ObservatoryX) -> Result[str, EX.JubError]:
        exists_result = await self.observatory_repository.get_by_id(observatory.observatory_id)
        if exists_result.is_ok:
            return Err(EX.JubError(f"Observatory with ID {observatory.observatory_id} already exists"))
        
        return await self.observatory_repository.insert(observatory)

    async def add_catalog(self, observatory_id: str, catalog_id: str,level:int = 0) -> Result[bool, EX.JubError]:
        """Assigns an existing catalog to this observatory (e.g., SPATIAL or CIE10)."""
        result = await self.graph_link_manager.link_observatory_to_catalog(observatory_id, catalog_id,level)
        if result.is_err:
            log.error(f"Failed to link catalog {catalog_id} to observatory {observatory_id}: {result.unwrap_err()}")
            return Err(EX.JubError(f"Failed to link catalog {catalog_id} to observatory {observatory_id}: {result.unwrap_err()}"))
        return Ok(True)
    # --- Read Operations (Aggregation) ---

    async def get_observatory(self, observatory_id: str) -> Result[MV4.ObservatoryX, EX.JubError]:
        return await self.observatory_repository.get_by_id(observatory_id)

    async def get_all_products_in_observatory(self, observatory_id: str) -> Result[List[MV4.ProductX], EX.JubError]:
        """
        Dynamically builds a $lookup pipeline to fetch all products for this domain.
        """
        pipeline = [
            {"$match": {"observatory_id": observatory_id}},
            {"$lookup": {
                "from": self.product_repository.collection.name, # Dynamic collection name
                "localField": "product_id",
                "foreignField": "product_id",
                "as": "product_data"
            }},
            {"$unwind": "$product_data"},
            {"$replaceRoot": {"newRoot": "$product_data"}}
        ]
        
        cursor = self.observatory_product_link_repository.collection.aggregate(pipeline)
        try:
            return Ok([MV4.ProductX(**doc) for doc in cursor])
        except Exception as e:
            log.error(f"Error fetching products in observatory: {e}")
            return Err(EX.UnknownError(str(e)))

    async def get_catalogs_by_observatory_id(self, observatory_id: str) -> Result[List[MV4.CatalogX], EX.JubError]:
        """
        Dynamically builds a $lookup pipeline to fetch all catalogs assigned to this domain.
        Executes asynchronously using motor.
        """
        try:
            print("BEFORE_PIPELINE")
            pipeline = [
                # 1. Find all link documents for this specific observatory
                {"$match": {"observatory_id": observatory_id}},
                
                # 2. Join the actual catalog documents
                {"$lookup": {
                    "from": CollectionNames.CATALOGS.value, # Dynamic collection name
                    "localField": "catalog_id",
                    "foreignField": "catalog_id",
                    "as": "catalog_data"
                }},
                
                # 3. Flatten the array created by $lookup
                {"$unwind": "$catalog_data"},
                
                # 4. Replace the root link document with the actual catalog metadata
                {"$replaceRoot": {"newRoot": "$catalog_data"}}
            ]
            
            # Execute against the linking collection
            cursor = self.graph_link_manager.observatory_catalog_link_repository.collection.aggregate(pipeline)
            documents = await cursor.to_list(length=None)
            
            # Parse into Pydantic models
            catalogs = [MV4.CatalogX(**doc) for doc in documents]
            return Ok(catalogs)
            
        except Exception as e:
            log.error({
                "message": "Error fetching catalogs for observatory",
                "error": str(e),
                "observatory_id": observatory_id
            })
            return Err(EX.JubError.from_exception(e)) 
    


    # --- Delete Operations ---

    async def delete_observatory(self, observatory_id: str) -> Result[bool, EX.JubError]:
        """Deletes the observatory (products remain in the database, just unassigned to this view)."""
        success = await self.observatory_repository.delete(observatory_id)
        return success

class CatalogService:
    def __init__(
        self, 
        catalog_repository: RV4.CatalogRepository, 
        catalog_items_repository: RV4.CatalogItemRepository,
        catalog_item_alias_repository: RV4.CatalogItemAliasRepository, # The alias/value repo
        link_manager: RV4.GraphLinkManager
    ):
        self.catalog_repository            = catalog_repository
        self.catalog_item_repository       = catalog_items_repository
        self.catalog_item_alias_repository = catalog_item_alias_repository
        self.link_manager                  = link_manager

    # --- Create Operations ---

    async def create_catalog(self, catalog: MV4.CatalogX) -> Result[str,EX.JubError]:
        exists_result = await self.catalog_repository.get_by_id(catalog.catalog_id)
        if exists_result.is_ok:
            return Err(EX.AlreadyExists(f"Catalog with ID {catalog.catalog_id} already exists"))
        return await self.catalog_repository.insert(catalog)

    async def add_item_to_catalog(self, catalog_id: str, item: MV4.CatalogItemX, parent_id: Optional[str] = None) -> Result[str,EX.JubError]:
        """Saves a new item, links it to its catalog, and builds the hierarchy if requested."""
        insert_rest = await self.catalog_item_repository.insert(item)

        if insert_rest.is_err:
            log.error({
                "message": "Failed to insert catalog item",
                "error": insert_rest.unwrap_err(),
                "catalog_id": catalog_id,
            })
            return Err(EX.JubError(f"Failed to insert catalog item: {insert_rest.unwrap_err()}"))
        
        item_id = insert_rest.unwrap()
        
        # Link to the main catalog (e.g., SPATIAL)
        result = await self.link_manager.link_catalog_to_item(catalog_id, item_id)
        if result.is_err:
            # Rollback item insertion if linking fails
            delete_catalog_item_result = await self.catalog_item_repository.delete(item_id)

            if delete_catalog_item_result.is_err:
                log.error(f"Failed to rollback catalog item after link failure: {delete_catalog_item_result.unwrap_err()}")
                return Err(EX.JubError(f"Failed to rollback catalog item after link failure: {delete_catalog_item_result.unwrap_err()}"))

            return Err(EX.JubError(f"Failed to link item to catalog: {result.unwrap_err()}"))
        
        # Link to parent if it exists (e.g., TAM -> VIC)
        if parent_id:
            await self.link_manager.set_item_relationship(parent_id, item_id)
            
        return Ok(item_id)

    async def add_value_to_item(self, catalog_item_id: str, value: MV4.CatalogItemAlias) -> Result[str,EX.JubError]:
        """Saves an alias (e.g., '1' or 'CDVALLES') and links it to the canonical item."""
        try: 
            val_id_result = await self.catalog_item_alias_repository.insert(value)
            if val_id_result.is_err:
                log.error(f"Failed to insert catalog item alias: {val_id_result.unwrap_err()}")
                return Err(EX.JubError(f"Failed to insert catalog item alias: {val_id_result.unwrap_err()}"))
            
            val_id = val_id_result.unwrap()
            
            res = await self.link_manager.link_item_to_alias(catalog_item_id, val_id)
            if res.is_err:
                # Rollback alias insertion if linking fails
                delete_alias_result = await self.catalog_item_alias_repository.delete(val_id)

                if delete_alias_result.is_err:
                    log.error(f"Failed to rollback catalog item alias after link failure: {delete_alias_result.unwrap_err()}")
                    return Err(EX.JubError(f"Failed to rollback catalog item alias after link failure: {delete_alias_result.unwrap_err()}"))

                return Err(EX.JubError(f"Failed to link alias to catalog item: {res.unwrap_err()}"))
            return Ok(val_id)
        except Exception as e:
            log.error(f"Error adding value to item: {e}")
            return Err(EX.JubError.from_exception(e))
    
    async def get_catalog_hierarchy_levels(self, root_catalog_id: str) -> Result[List[MV4.CatalogX], EX.JubError]:
        """
        Gets the structural hierarchy for a SPECIFIC catalog family.
        Example: Pass "cat_cie10", get [Capítulo, Bloque, Categoría] in exact order.
        Example: Pass "cat_spatial_mx", get [País, Estado, Municipio] in exact order.
        """
        try:
            # We instantly grab the whole family and sort by level (0, 1, 2, 3...)
            cursor = self.catalog_repository.collection.find(
                {"root_catalog_id": root_catalog_id}
            ).sort("level", 1)
            
            docs = await cursor.to_list(length=None)
            return Ok([MV4.CatalogX(**doc) for doc in docs])
            
        except Exception as e:
            return Err(EX.JubError.from_exception(e))

    async def get_items_by_parent(self, parent_item_id: str) -> Result[List[MV4.CatalogItemX], EX.JubError]:
        """
        Gets the specific sub-level items.
        Example: Pass "MX" (Mexico), get all States linked to it.
        """
        try:
            # 1. Find all children edges in the relationship collection
            rel_cursor = self.link_manager.catalog_item_relationship_repository.collection.find({"parent_id": parent_item_id})
            rel_docs = await rel_cursor.to_list(length=None)
            
            if not rel_docs:
                return Ok([])
                
            child_ids = [doc["child_id"] for doc in rel_docs]
            
            # 2. Fetch the actual CatalogItem metadata for those children
            item_cursor = self.catalog_item_repository.collection.find({"catalog_item_id": {"$in": child_ids}})
            item_docs = await item_cursor.to_list(length=None)
            
            items = [MV4.CatalogItemX(**doc) for doc in item_docs]
            items.sort(key=lambda x: x.name) # Alphabetical for the UI
            
            return Ok(items)
        except Exception as e:
            return Err(EX.JubError.from_exception(e))
    # --- Delete Operations (Cascading) ---

    async def delete_catalog_item(self, catalog_item_id: str) -> Result[bool, EX.JubError]:
        """Deletes an item and securely wipes its tags, aliases, and hierarchy edges."""
        success = await self.catalog_item_repository.delete(catalog_item_id)
        if success:
            await self.link_manager.remove_all_catalog_item_links(catalog_item_id)
        return success

    async def delete_catalog(self, catalog_id: str) -> Result[bool, EX.JubError]:
        """Deletes a catalog and its direct links."""
        success = await self.catalog_repository.delete(catalog_id)
        if success:
            await self.link_manager.remove_all_catalog_links(catalog_id)
        return success


    
class ProductService:
    def __init__(
        self, 
        product_repository: RV4.ProductRepository, 
        link_manager: RV4.GraphLinkManager
    ):
        self.product_repository = product_repository
        self.link_manager = link_manager

    async def insert_product(
        self, 
        product: MV4.ProductX, 
        observatory_id: str, 
        catalog_item_ids: List[str] = None
    ) -> Result[str, EX.JubError]:
        """Inserts a dataset, assigns it to an observatory, and applies all its tags."""
        
        # 1. Save the product
        prod_res = await self.product_repository.insert(product)
        if prod_res.is_err:
            return prod_res

        # 2. Assign to the observatory
        obs_link_res = await self.link_manager.link_observatory_to_product(observatory_id, product.product_id)
        if obs_link_res.is_err:
            return obs_link_res

        # 3. Apply the tags
        if catalog_item_ids:
            for item_id in catalog_item_ids:
                tag_res = await self.link_manager.link_product_to_catalog_item(product.product_id, item_id)
                if tag_res.is_err:
                    log.warning(f"Failed to tag product {product.product_id} with {item_id}: {tag_res.err()}")
                    # Depending on your strictness, you could return an Err here, 
                    # but usually, you want to keep going even if one tag fails.

        return Ok(product.product_id)

    async def delete_product(self, product_id: str) -> Result[bool, EX.JubError]:
        """Deletes the product and securely wipes its observatory assignment and tags."""
        del_res = await self.product_repository.delete(product_id)
        if del_res.is_err:
            return del_res
            
        wipe_res = await self.link_manager.remove_all_product_links(product_id)
        if wipe_res.is_err:
            return wipe_res
            
        return Ok(True)


class SearchService:
    def __init__(
        self, 
        observatory_product_link_repository:RV4.ObservatoryToProductLinkRepository,
        product_catalog_item_link_repository: RV4.ProductToCatalogItemLinkRepository,
        catalog_item_relationship_repository: RV4.CatalogItemRelationshipRepository,
        catalog_item_repository: RV4.CatalogItemRepository,
        product_repository: RV4.ProductRepository,
        catalog_alias_repository: RV4.CatalogItemAliasRepository,
        catalog_item_catalog_alias_link_repository: RV4.CatalogItemToCatalogAliasLinkRepository
    ):
        self.observatory_product_link_repository  = observatory_product_link_repository
        self.product_catalog_item_link_repository = product_catalog_item_link_repository
        self.catalog_item_relationship_repository = catalog_item_relationship_repository
        self.catalog_item_repository              = catalog_item_repository
        self.product_repository                   = product_repository
        self.catalog_alias_repository             = catalog_alias_repository
        self.catalog_item_catalog_alias_link_repository = catalog_item_catalog_alias_link_repository
        
    async def _get_canonical_id(self, raw_target: str) -> Result[str, EX.JubError]:
            """
            Intercepts a raw string from the AST. 
            If it's an alias (e.g., '28'), it returns the real ID (e.g., 'TAM').
            If it's not an alias, it assumes it's already the real ID.
            """
            try:
                # 1. Search the alias table for this exact string
                alias_cursor = self.catalog_alias_repository.collection.find({"value": raw_target})
                alias_docs = await alias_cursor.to_list(length=1)
                
                if alias_docs:
                    alias_id = alias_docs[0]["catalog_item_alias_id"]
                    
                    # 2. Find which canonical item this alias points to
                    link_cursor = self.catalog_item_catalog_alias_link_repository.collection.find({"catalog_item_alias_id": alias_id})
                    link_docs = await link_cursor.to_list(length=1)
                    
                    if link_docs:
                        return Ok(link_docs[0]["catalog_item_id"])
                        
                # 3. If it's not in the alias table, we assume the user typed the canonical ID directly
                return Ok(raw_target)
                
            except Exception as e:
                log.error(f"Error resolving alias for {raw_target}: {e}")
                return Err(EX.JubError.from_exception(e))       
    def __is_global_wildcard(self, condition: Condition) -> bool:
            """Checks if the user just passed '*' with no prefix (e.g., VS(*))."""
            path = condition.item_path
            # Check for strings "*", "", or lists ["*"], []
            if isinstance(path, list):
                return len(path) == 0 or (len(path) == 1 and path[0] == "*")
            return path == "*" or path == ""
    async def execute_query(self, query_str: str, observatory_id: Optional[str] = None) -> Result[List[MV4.ProductX], EX.JubError]:
        """
        The main entry point for the Jub search bar.
        """
        try:
            # 1. Parse string to AST
            ast = QueryAST.parse(query_str)
            print("AST",ast)
            # 2. Resolve AST conditions into required sets of Catalog Item IDs
            required_sets_res = await self._build_required_sets(ast)
            print(required_sets_res)

            print("_"*20)
            if required_sets_res.is_err:
                return required_sets_res
            
            required_sets = required_sets_res.unwrap()
            
            # 3. Build and execute the aggregation pipeline
            pipeline = self._build_mongo_pipeline(observatory_id, required_sets)
            
            cursor = self.observatory_product_link_repository.collection.aggregate(pipeline)
            documents = await cursor.to_list(length=None)
            
            # 4. Return formatted products
            products = [MV4.ProductX(**doc) for doc in documents]
            return Ok(products)
            
        except Exception as e:
            log.error(f"Execution failed for query '{query_str}': {e}")
            return Err(EX.JubError.from_exception(e))

    async def _build_required_sets(self, ast: QueryAST) -> Result[List[List[str]], EX.JubError]:
        """
        Converts the AST into a list of required tag lists.
        A product MUST have at least one matching tag from EVERY list in required_sets.
        """
        try: 
            required_sets: List[List[str]] = []
            for query in ast.queries:
                # If OR/SINGLE logic: All conditions pool together into ONE requirement set.
                if query.group.logic in ["OR", "SINGLE"]:
                    # We combine all conditions into one big set. The product needs at least one tag from this combined set to satisfy the OR logic.
                    combined_set = []
                    # skip_group is a flag to identify if we have a global wildcard in the group. If we do, we can skip processing the rest of the conditions because the wildcard already allows any tag to match.
                    skip_group = False
                    for cond in query.group.conditions:
                        if self.__is_global_wildcard(cond):
                            skip_group = True
                            break
                        # If it's not a global wildcard, we resolve the condition as normal and add its valid tags to the combined set.
                        res = await self._resolve_condition(cond)
                        if res.is_err: 
                            log.error(f"Failed to resolve condition {cond}: {res.unwrap_err()}")
                            return res
                        # combined_set.extend(res.unwrap())
                        combined_set.update(res.unwrap()) # Using a set to avoid duplicates

                    if not skip_group:
                        required_sets.append(list(combined_set))
                    
                # If AND logic: Every condition becomes its OWN separate requirement set.
                elif query.group.logic == "AND":
                    intersected_sets = None

                    for cond in query.group.conditions:
                        
                        if self.__is_global_wildcard(cond):
                            continue  # Skip this condition, it doesn't restrict the search

                        res = await self._resolve_condition(cond)
                        if res.is_err: 
                            log.error(f"Failed to resolve condition {cond}: {res.unwrap_err()}")
                            return res
                        conds_ids = set(res.unwrap())

                        if intersected_sets is None:
                            intersected_sets = conds_ids
                        else:                            
                            intersected_sets = intersected_sets.intersection(conds_ids)

                    if intersected_sets is not None:
                        required_sets.append(list(intersected_sets))

            # print("REQUIRED",required_sets)
            return Ok(required_sets)
        except Exception as e:
            log.error({
                "message": "Error building required sets from AST",
                "error": str(e),
            })
            return Err(EX.JubError.from_exception(e))

    async def _resolve_condition(self, condition: Condition) -> Result[List[str], EX.JubError]:
        """
        Translates a single AST condition into an exact list of catalog_item_ids.
        """
        try:
            log.debug({
                "event":"CONDITION_RESOLUTION",
                "message": "Resolving condition",
                "condition": condition.model_dump()
            })
            if condition.catalog_value == "TEMPORAL" and condition.operator not in ["WILDCARD"]:
                mongo_op_map = {
                    ">": "$gt", ">=": "$gte", "<": "$lt", "<=": "$lte", "=": "$eq",
                    "EXACT": "$eq" 
                }
                mongo_op     = mongo_op_map.get(condition.operator)
                if not mongo_op:
                    return Err(EX.UnknownError(f"Unsupported operator for temporal condition: {condition.operator}"))

                path_val = condition.item_path[-1] if isinstance(condition.item_path, list) and len(condition.item_path) > 0 else condition.item_path
                
                try:
                    dt_val = DT.datetime.fromisoformat(path_val.replace("Z", "+00:00"))  # Convert ISO string to datetime object
                except ValueError as ve:
                    log.error(f"Invalid datetime format for temporal condition: {path_val}")
                    return Err(EX.JubError(f"Invalid datetime format for temporal condition: {path_val}"))


                # Query the catalog items to find which IDs fall in this date range
                cursor = self.catalog_item_repository.collection.find(
                    # Assuming temporal values are stored as ISO strings in 'value'
                    {"value_type": "DATETIME", "temporal_value": {mongo_op: dt_val}}
                )
                docs = await cursor.to_list(length=None)
                log.debug({
                    "event": "TEMPORAL_CONDITION_RESOLUTION",
                    "message": "Resolved temporal condition",
                    "path_val": path_val,
                    "mongo_op": mongo_op,
                    "dt_val": dt_val.isoformat(),
                    "condition": condition.model_dump(),
                    "resolved_ids": [doc["catalog_item_id"] for doc in docs]
                })
                return Ok([doc["catalog_item_id"] for doc in docs])


            path       = condition.item_path
            is_list    = isinstance(path, list)
            raw_target = ""
            # Extract target ID from the path (e.g., "CIE10.C50" -> "C50")
            # target_id = condition.item_path[-1] if isinstance(condition.item_path, list) else condition.item_path


            # Handle EXACT
            log.debug({
                "event": "CONDITION_RESOLUTION",
                "message": "Handling exact condition",
                "operator": condition.operator,
                "item_path": condition.item_path
            })
            if condition.operator == "WILDCARD":
                path_len = len(path)
                if is_list:
                    # Scenario A: The parser left the '*' in the list (e.g., ['MX', 'TAMPS', '*'])
                    if path_len > 1 and path[-1] == "*":
                        raw_target = path[-2]
                    # Scenario B: The parser stripped the '*' (e.g., ['MX', 'TAMPS'])
                    elif path_len > 0 and path[-1] != "*":
                        raw_target = path[-1]
                    # Scenario C: Reverse wildcard (e.g., ['*', 'MX'])
                    elif path_len > 0 and path[0] == "*":
                        raw_target = path[-1]
                    else:
                        return Err(EX.JubError(f"Invalid wildcard list format: {path}"))
                else:
                    # Handle raw strings
                    if path.endswith(".*"):
                        raw_target = path[:-2]
                    elif path != "*":
                        raw_target = path  # The parser just sent "TAMPS" with a WILDCARD operator
                    else:
                        raw_target = path # Global wildcard handling

                # return Err(EX.JubError(f"Invalid wildcard format in condition: {condition}"))
            elif condition.operator == "EXACT":
                raw_target = path[-1] if is_list else path
            else:
                return Err(EX.UnknownError(f"Unsupported operator in condition: {condition.operator}"))



            # Alias resolution: If the user typed an alias (e.g., '28'), we need to find the canonical ID (e.g., 'TAM') 
            canonical_res = await self._get_canonical_id(raw_target)
            
            if canonical_res.is_err:
                log.error(f"Failed to resolve canonical ID for {raw_target}: {canonical_res.unwrap_err()}")
                return Err(EX.JubError(f"Failed to resolve canonical ID for {raw_target}: {canonical_res.unwrap_err()}"))
            target_id = canonical_res.unwrap()

            if condition.operator == ConditionOperators.WILDCARD.value:
                children_res = await self.catalog_item_relationship_repository.get_all_children_nodes(target_id)
                if children_res.is_err:
                    log.error(f"Failed to fetch children for wildcard condition {condition}: {children_res.unwrap_err()}")
                    return Err(EX.JubError(f"Failed to fetch children for wildcard condition {condition}: {children_res.unwrap_err()}"))
                valid_ids = [target_id] + children_res.unwrap()  # Include the parent ID itself
                return Ok(valid_ids)
            
            elif condition.operator == ConditionOperators.EXACT.value:
                return Ok([target_id])
            
            else:
                log.error(f"Unsupported operator in condition: {condition.operator}")
                return Err(EX.UnknownError(f"Unsupported operator in condition: {condition.operator}"))
           

        except Exception as e:
            log.error(f"Error resolving condition {condition}: {e}")
            return Err(EX.JubError.from_exception(e))

    def _build_mongo_pipeline(self, observatory_id: Optional[str], required_sets: List[List[str]]) -> List[dict]:
        """
        Translates the required_sets into a high-performance MongoDB intersection pipeline.
        If observatory_id is None, it searches across all observatories.
        """
        pipeline = []

        # 1. Scope the search strictly to this observatory (IF provided)
        if observatory_id:
            pipeline.append({"$match": {"observatory_id": observatory_id}})
            
        # 1.5. DEDUPLICATION: If searching all observatories, a product might appear multiple times 
        # if it belongs to multiple observatories. We group by product_id to ensure unique results.
        pipeline.append({
            "$group": {
                "_id": "$product_id",
                "product_id": {"$first": "$product_id"}
            }
        })

        # 2. Join the product's tags from the linking table
        pipeline.append({
            "$lookup": {
                "from": self.product_catalog_item_link_repository.collection.name,
                "localField": "product_id",
                "foreignField": "product_id",
                "as": "raw_tags"
            }
        })

        # 3. Transform the array of link objects into a simple array of strings (IDs)
        pipeline.append({
            "$project": {
                "product_id": 1,
                "matched_tags": {
                    "$map": {
                        "input": "$raw_tags",
                        "as": "tag_doc",
                        "in": "$$tag_doc.catalog_item_id"
                    }
                }
            }
        })

        # 4. Apply the logical intersections parsed from the AST (ONLY if there are requirements)
        if required_sets:
            intersection_conditions = [
                {"$gt": [{"$size": {"$setIntersection": ["$matched_tags", req_set]}}, 0]}
                for req_set in required_sets
            ]
            
            pipeline.append({
                "$match": {
                    "$expr": {
                        "$and": intersection_conditions
                    }
                }
            })

        # 5. Fetch the actual product metadata for the surviving IDs
        pipeline.extend([
            {"$lookup": {
                "from": self.product_repository.collection.name,
                "localField": "product_id",
                "foreignField": "product_id",
                "as": "product_data"
            }},
            {"$unwind": "$product_data"},
            {"$replaceRoot": {"newRoot": "$product_data"}}
        ])

        return pipeline