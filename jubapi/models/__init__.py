
from pydantic import BaseModel,Field, ConfigDict
from typing import List, Optional,Dict
from bson import ObjectId
from enum import Enum


class PyObjectId(ObjectId):
    """Custom ObjectId class to handle BSON ObjectId."""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type):
        from pydantic import GetCoreSchemaHandler
        from pydantic_core import core_schema

        # Ensure ObjectId is treated as a string when validating
        return core_schema.with_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)




class LevelCatalog(BaseModel):
    level: int = Field(..., description="The hierarchical level index for this catalog within the observatory.")
    cid: str = Field(...,description="The unique Catalog ID associated with this specific level.")


class Observatory(BaseModel):
    obid:str=Field(default="", description="Unique identifier for the observatory.")
    title: str= Field(default="Observatory", description="Display tittle or name of the observatory shown in the UI.")
    image_url:str= Field(default="", description="URL pointing to the representative image for the observatory.")
    description:str= Field(default="", description="Detailed description of the observatory's scope")
    catalogs:List[LevelCatalog]= Field(default=[],description="List mapping specific catalogs to hierarchical levels within this observatory.")
    disabled:bool = Field(default=False, description="Flag indicating if the observatory is currently hidden or disabled for external consumers.")

    model_config = ConfigDict(

        json_schema_extra = {
            "example": {
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
        }
    )


class CatalogItem(BaseModel):
    value:str = Field(...,description="The internal string value if the catalog item.")
    display_name:str = Field(...,description="The readable name of the item shown in the UI.")
    code:int = Field(...,description="Numeric code associated with the catalog item.")
    description:str = Field(...,description="Detailed description of what this item represents.")
    metadata:Dict[str,str] = Field(..., description="Additional key-value metadata for the item.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "value": "<String>",
                "display_name": "<String>",
                "code": "<Integer>",
                "description": "<String>",
                "metadata": {
                    "<String>": "<String>"
                }
            }
        }
    )


class CatalogKind(str, Enum):
    INTEREST = "INTEREST"
    TEMPORAL = "TEMPORAL"
    SPATIAL  = "SPATIAL"

class Catalog(BaseModel):
    cid:str = Field(default="", description="The unique identifier for the observatory.")
    display_name:str = Field(default="", description="The readable name of the item shown in the UI.")
    items: List[CatalogItem] = Field(default = [], description="List of items contained within this catalog")
    kind:CatalogKind = Field(..., description="The categorization of the catalog (INTEREST, TEMPORAL, SPATIAL).")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "cid": "<String>",
                "display_name": "<String>",
                "kind": "<String>",
                "items": [
                    {
                        "value": "<String>",
                        "display_name": "<String>",
                        "code": "<Integer>",
                        "description": "<String>",
                        "metadata": {}
                    }
                ]
            }
        }
    )


class Level(BaseModel):
    index:int = Field(..., description="The depth index of this level within the product's hierarchy.")
    cid:str = Field(..., description="The Catalog ID that this level is associated with.")
    value:str = Field(..., description="The specific CatalogItem value selected for this level.")
    kind:str = Field(default="", description="The kind of catalog this level represents (INTEREST, TEMPORAL, SPATIAL).")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "index": "<Integer>",
                "cid": "<String>",
                "value": "<String>",
                "kind": "<String>"
            }
        }
    )

class Product(BaseModel):
    pid:str = Field(default="", description="Unique identifier for the product.")
    description:str= Field(default="", description="A comprehensive description of the product and its data.")
    levels:List[Level]=Field(default=[], description="List of hierarchical levels defining the product's  categorizaation.")
    product_type: str=Field(default="", description="The classification or type of the product.")
    level_path:str=Field(default="", description="A materialized path string representing the hierarchy of levels for quick regex search.")
    profile:str=Field(default="", description="The profile or scope under which this product falls.")
    product_name: str=Field(default="", description="The display name of the product.")
    tags:List[str]=Field(default=[], description="A list of searchable keyword tags associated with the product.")
    url:str = Field(default="", description="The direct URL or endpoint to access the product's source")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
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
        }
    )
