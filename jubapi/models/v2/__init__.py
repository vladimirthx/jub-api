from pydantic import BaseModel, Field,StringConstraints,AfterValidator
from typing import Optional, Dict, Annotated
from enum import Enum
import re

import datetime as DT



def to_upper_snake(v: str) -> str:
    v = re.sub(r'([a-z])([A-Z])', r'\1_\2', v)
    v = re.sub(r'[^A-Za-z0-9]+', '_', v)
    r = v.upper().strip('_')
    return r

UpperSnakeStr =Annotated[str, 
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
    AfterValidator(to_upper_snake)
]


class TimestampedModel(BaseModel):
   created_at: DT.datetime = Field(default_factory=lambda: DT.datetime.now(DT.timezone.utc))
   updated_at: DT.datetime = Field(default_factory=lambda: DT.datetime.now(DT.timezone.utc))


class Descriptable(TimestampedModel):
  description: Optional[str] = Field(default="")
  metadata: Optional[Dict[str, str]] = Field(default_factory=dict)

class ObservatoryX(Descriptable):
  observatory_id: str
  title: str

 
class ProductX(Descriptable):
    product_id: str
    name: str
   

class CatalogItemValueType(str, Enum):
    STRING   = "STRING"
    NUMBER   = "NUMBER"
    BOOLEAN  = "BOOLEAN"
    DATETIME = "DATETIME"



class CatalogItemAlias(Descriptable):
    catalog_item_alias_id: str
    value: str
    value_type: CatalogItemValueType

class CatalogItemX(Descriptable):
  catalog_item_id: str
  name: str
  value: UpperSnakeStr
  code: int
  value_type: CatalogItemValueType
  temporal_value: Optional[DT.datetime] = None



class CatalogType(str, Enum):
    INTEREST   = "INTEREST"
    TEMPORAL   = "TEMPORAL"
    SPATIAL    = "SPATIAL"
    OBSERVABLE = "OBSERVABLE"
    REFERENCE  = "REFERENCE"


class CatalogX(Descriptable):
    catalog_id: str
    root_group_id: Optional[str ] = Field(default=None)
    name: str
    value: UpperSnakeStr 
    catalog_type: CatalogType
    parent_catalog_id: Optional[str] = None
    level: int = 0
    
# Links

class CatalogItemToProductLink(TimestampedModel):
    product_id: str
    catalog_item_id: str
class CatalogToCatalogItemLink(TimestampedModel):
  catalog_id: str
  catalog_item_id: str
  
class CatalogItemToCatalogAliasLink(TimestampedModel):
    catalog_item_id: str
    catalog_item_alias_id: str
class CatalogItemRelationship(TimestampedModel):
    parent_id: str # e.g., ID for "MX"
    child_id: str  # e.g., ID for "SLP"
class ObservatoryToProductLink(TimestampedModel):
  observatory_id: str
  product_id: str
  
class ObservatoryToCatalogLink(TimestampedModel):
  observatory_id: str
  catalog_id: str 
  level:int=0

