#Current Data Model

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



## 3. Pain Points & Proposed Solutions

Summary of critical issues identified in the current architecture and how the new ERM will resolve them.

### **1. Catalog Bloat**

* **Problem:** Embedding items increases document size significantly, forcing the database to handle heavier I/O operations. This leads to frequent memory re-allocations and complex index updates.





### **2. Inefficient Links (Observatory Updates)**

* **Problem:** When a Catalog contains thousands of items, the parent document becomes massively bloated. Any update to a single item requires rewriting and re-indexing the entire Catalog document, creating a write bottleneck.




### **3. Search Constraints (Product Querying)**

* **Problem:** Embedding `Level` objects within the `Product` document complicates search. Finding products linked to a specific Catalog Item requires slow, complex queries that must traverse embedded arrays.

