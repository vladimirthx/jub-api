from enum import Enum
class CollectionNames(Enum):
    """Centralized collection names for MongoDB."""
    OBSERVATORIES                    = "observatories"
    PRODUCTS                         = "products"
    CATALOGS                         = "catalogs"
    CATALOG_ITEMS                    = "catalog_items"
    CATALOG_ITEM_VALUES              = "catalog_item_values"
    OBSERVATORY_PRODUCT_LINKS        = "observatory_product_links"
    PRODUCT_CATALOGS_ITEM_LINKS      = "product_catalogs_item_links"
    CATALOG_ITEM_RELATIONSHIPS       = "catalog_item_relationships"
    CATALOG_CATALOG_ITEM_LINKS       = "catalog_catalog_item_links"
    CATALOG_ITEM_CATALOG_ALIAS_LINKS = "catalog_item_catalog_alias_links"
    OBSERVATORY_CATALOG_LINKS        = "observatory_catalog_links"
