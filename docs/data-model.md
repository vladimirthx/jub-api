# Data Model

## 1. Current JSON Schemas
Below are the JSON structures for the core entities based on the V1 (`catalog.py`, `observatory.py`, `product.py`). The fields causing performance issues due to embedding are highlighted.

### **Catalog**

The `Catalog` entity embeds all its items directly within a single document.



```json
{
    "cid": "<String>",
    "display_name": "<String>",
    "kind": "<String>",
    "items:" [
        {
            "value": "<String>",
            "display_name": "<String>",
            "code": "<Integer>",
            "description": "<String>",
            "metadata": {

            }
            

        }
    ]
}
```

### **Observatory**

The `Observatory` entity embeds a list of `LevelCatalogDTO` objects to define which catalogs belong to which level, rather than using relational references.

```json
{
  "obid": "string",
  "title": "string",
  "description": "string",
  "image_url": "string",
  "catalogs": [ // <--- Embedded List
    {
      "level": 0,
      "cid": "string"
    }
  ]
}

```

### **Product**

The `Product` entity embeds its hierarchical levels directly. It lacks a direct foreign key to the Observatory, relying instead on a complex `level_path` or embedded `levels` array for association.

```json
{
  "pid": "string",
  "product_name": "string",
  "product_type": "string",
  "level_path": "string",
  "levels": [ // <--- Embedded List
    {
      "index": 0,
      "cid": "string",
      "value": "string",
      "kind": "string"
    }
  ],
  "profile": "string",
  "url": "string",
  "tags": []
}

```

## 2. Map the current API use cases
Analysis of the existing API endpoints and their interaction with the databse, hightlighting the performance of the current embedded model.

### **Create a Catalog**
* **Step-by-Step Analysis:**
1. **Request Reception:** The API receives a full `Catalog` JSON object. THis object containd the `cid`, metadata, and the entire list of `items` embedded within it.

2. **Validation:** The service calls `find_by:cid` to verify if the catalog ID already exists.

3. **Single Massive Write:** If valid, the `catalog_service.create` method writes the entire object to the `catalogs` collection.

4. **Implication:** When a catalog has 1,000 items, the database performs a single, heavy I/O write operation for one massive document. This triggers complex index updates for the parent document regarding slow writes due to increased size.


### **Update a Catalog Item**


* **Step-by-Step Analysis:**

1. **No Direct Access:** There is no endpoint to update a single item directly by its ID because items do not exist as standalone documents.

2. **Parent Retrieval:** To change one item's name, the system must first fetch the entire parent `Catalog` document into memory.

3. **Full Document Rewrite:** After modifying the item in the array, the system must update the entire `Catalog` document in the database.

4. **Implication:** Updating a single item requires rewriting and re-indexing a large catalog document, creating a significant write bottleneck.

### Fetch an Observatory's Products


* **Step-by-Step Analysis:**

1. **Request:** The API receives an `obid` (Observatory ID) and filters.

2. **Indirect Querying:** The Product entity lacks a direct `observatory_id` foreign key. Instead, it relies on an embedded `levels` array or a `level_path` string.

3. **Scanning:** The database must scan these embedded arrays (levels) across the product collection to find matches that correspond to the observatory's configuration.

4. **Implication:** This results in slow and complex queries because the engine must traverse embedded arrays rather than utilizing a simple, direct index lookup.


## 3. Pain Points & Proposed Solutions

Summary of critical issues identified in the current architecture and how the new ERM will resolve them.

### **1. Catalog Bloat**

* **Problem:** Embedding items increases document size significantly, forcing the database to handle heavier I/O operations. This leads to frequent memory re-allocations and complex index updates.

* **Proposed solution:**
  * Apply Entity Separation by create a Many-to-Many  (link collection)
  * Apply an Entity Separation by extract items from the embedded array into a new, independent primary collection called `CatalogItemLink` to connect `Catalog` and `CatalogItem`.
  * Refactoring the API. Instead of writing one large document, it must create the `Catalog` document and separately create the associated links in `CatalogItemLink`.






### **2. Inefficient Links (Observatory Updates)**

* **Problem:** When a Catalog contains thousands of items, the parent document becomes massively bloated. Any update to a single item requires rewriting and re-indexing the entire Catalog document, creating a write bottleneck.
* **Proposed solution:**
  * Remove embedded lists and manage the relationship using an `ObservatoryCatalogLink` collection (M:N); this link table will utilize a composite index of `(obid, cid)` to efficiently map to their Catalogs.
  * Update GET operations so that retrieving an Observatory involves querying the `ObservatoryCatalogLink` collection to find its associated Catalogs, rather than loading embedded arrays.






### **3. Search Constraints (Product Querying)**

* **Problem:** Embedding `Level` objects within the `Product` document complicates search. Finding products linked to a specific Catalog Item requires slow, complex queries that must traverse embedded arrays.
* **Proposed solution:**
  * Implement `ProductObservatoryLink` to directly link Products to Observatories and implement `ProductCatalogItemLink` to directly link Products to specific Catalog Items.
  * Refactor the `create_products` endpoint to parse input levels and create the corresponding entries in `ProductCatalogItemLink`, removing the embedded `levels` array from the `Product` document.


Some of this changes are going to be made by using a Data Migration Script. It will be developed to move existing data from `Catalog.items` into the decoupled `CatalogItems` collection, and also extract data from the embedded `Product.levels` fields and populate the new junction collections.

