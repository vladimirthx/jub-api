## OCA - API  v1
An observatory is an object that contain N catalogs. This object is used in the user interface to create a page dinamically. The catalogs are use to match products that are listed in the UI. We can use the values in the catalogs to create queries. You can se an example of an observatory at [here](https://muyal.tamps.cinvestav.mx/observatories). You need to have an account please contact me a at jesus.castillo.b@cinvestav.mx to request your account.

### Create observatory
* **Endpoint URL:** `/observatories`
* **HTTP Method:** `POST`
* **Required DTO:** `ObservatoryDTO`

**JSON Payload Structure:**
```json
{
  "obid": "<String>",
  "title": "<String>",
  "image_url": "<String>",
  "description": "<String>",
  "catalogs": [
    {
      "level": "<Integer>",
      "cid": "<String>"
    }
  ],
  "disabled": "<Boolean>"
}

```


### Create catalog

* **Endpoint URL:** `/catalogs`
* **HTTP Method:** `POST`
* **Required DTO:** `CatalogDTO`

**JSON Payload Structure:**
```json
{
  "cid": "<String>",
  "display_name": "<String>",
  "kind": "<String>", 
  "items": [
    {
      "value": "<String>",
      "display_name": "<String>",
      "code": "<Integer>",
      "description": "<String>",
      "metadata": {
        "<String>": "<String>"
      }
    }
  ]
}

```

### Assign catalog to observatory

* **Endpoint URL:** `/observatories/{obid}`
* **HTTP Method:** `POST`
* **Required DTO:** A list of `LevelCatalogDTO` objects

**JSON Payload Structure:**
```
[
  {
    "level": "<Integer>",
    "cid": "<String>"
  }
]

```

### Create products

* **Endpoint URL:** `/products`
* **HTTP Method:** `POST`
* **Required DTO:** A list of `ProductDTO` objects

**JSON Payload Structure:**
```json
[
  {
    "pid": "<String>",
    "product_name": "<String>",
    "product_type": "<String>",
    "description": "<String>",
    "level_path": "<String>",
    "levels": [
      {
        "index": "<Integer>",
        "cid": "<String>",
        "value": "<String>",
        "kind": "<String>"
      }
    ],
    "profile": "<String>",
    "tags": [
      "<String>"
    ],
    "url": "<String>"
  }
]

```

### Perform Queries of Products

* **Endpoint URL:** `/observatories/{obid}/products/nid`
* **HTTP Method:** `POST`
* **Required DTO:** `ProductFilter`

**JSON Payload Structure:**
```json
{
  "temporal": {
    "low": "<Integer>",
    "high": "<Integer>"
  },
  "spatial": {
    "country": "<String>",
    "state": "<String>",
    "municipality": "<String>"
  },
  "interest": [
    {
      "value": "<String>",
      "inequality": {
        "gt": "<Integer>"
      }
    }
  ],
  "tags": [
    "<String>": "<String>"
  ]
}

```



## OCA - API v2