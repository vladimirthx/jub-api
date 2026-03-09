
from pydantic import BaseModel,Field, ConfigDict
from typing import List, Dict
from bson import ObjectId
from enum import Enum


class PyObjectId(ObjectId):
    """Custom ObjectId class to handle BSON ObjectId.
    This class provides the necessary schema handling and validation for 
    using MongoDB ObjectIds within Pydantic models.
    
    """
    
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type):
        """
        Returns the Pydantic core schema for the ObjectId.

        Ensures that the ObjectId is treated as a string when validating.

        Args:
            _source_type: The source type being validated.

        Returns:
            A Pydantic core schema with a plain validator function.
        """
        from pydantic import GetCoreSchemaHandler
        from pydantic_core import core_schema

        # Ensure ObjectId is treated as a string when validating
        return core_schema.with_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, value):
        """
        Validates if the provided value is a valid BSON ObjectId.

        Args:
            value (str | ObjectId): The value to validate.

        Returns:
            ObjectId: The validated BSON ObjectId object.

        Raises:
            ValueError: If the provided value is not a valid ObjectId.
        """
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)




class LevelCatalog(BaseModel):
    """
    Maps a specific catalog to a hierarchical level within an observatory.

    Attributes:
    level (int): The hierarchical level index for this catalog within the observatory.
    cid (str): The unique Catalog ID associated with this specific level.
    """
    level: int = Field(..., description="The hierarchical level index for this catalog within the observatory.")
    cid: str = Field(...,description="The unique Catalog ID associated with this specific level.")


class Observatory(BaseModel):
    """
    Represents an observatory which acts as a collection of catalogs.

    Attributes:
        obid (str): Unique identifier for the observatory.
        title (str): Display title or name of the observatory shown in the UI.
        image_url (str): URL pointing to the representative image for the observatory.
        description (str): Detailed description of the observatory's scope.
        catalogs (List[LevelCatalog]): List mapping specific catalogs to hierarchical levels within this observatory.
        disabled (bool): Flag indicating if the observatory is currently hidden or disabled for external consumers.
    """
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
    """
    Represents an individual item or entry within a catalog.

    Attributes:
        value (str): The internal string value of the catalog item.
        display_name (str): The readable name of the item shown in the UI.
        code (int): Numeric code associated with the catalog item.
        description (str): Detailed description of what this item represents.
        metadata (Dict[str, str]): Additional key-value metadata for the item.
    """
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

    # @field_validator('value', mode='before')




class CatalogKind(str, Enum):
    """
    Defines the categorization kind of a catalog.
    
    Attributes:
        INTEREST: Represents an interest-based catalog.
        TEMPORAL: Represents a temporal or time-based catalog.
        SPATIAL: Represents a spatial or location-based catalog.
    """
    INTEREST = "INTEREST"
    TEMPORAL = "TEMPORAL"
    SPATIAL  = "SPATIAL"

class Catalog(BaseModel):
    """
    Represents a collection of items grouped by a specific categorization kind.

    Attributes:
        cid (str): The unique identifier for the catalog.
        display_name (str): The readable name of the catalog shown in the UI.
        items (List[CatalogItem]): List of items contained within this catalog.
        kind (CatalogKind): The categorization of the catalog (INTEREST, TEMPORAL, SPATIAL).
    """
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
    """
    Represents a specific depth and associated catalog value in a product's hierarchy.

    Attributes:
        index (int): The depth index of this level within the product's hierarchy.
        cid (str): The Catalog ID that this level is associated with.
        value (str): The specific CatalogItem value selected for this level.
        kind (str): The kind of catalog this level represents (INTEREST, TEMPORAL, SPATIAL).
    """
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
    """
    Represents a product and its hierarchical classification data.

    Attributes:
        pid (str): Unique identifier for the product.
        description (str): A comprehensive description of the product and its data.
        levels (List[Level]): List of hierarchical levels defining the product's categorization.
        product_type (str): The classification or type of the product.
        level_path (str): A materialized path string representing the hierarchy of levels for quick regex search.
        profile (str): The profile or scope under which this product falls.
        product_name (str): The display name of the product.
        tags (List[str]): A list of searchable keyword tags associated with the product.
        url (str): The direct URL or endpoint to access the product's source.
    """
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
