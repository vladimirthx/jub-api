import re
from typing import List, Union
from pydantic import BaseModel
from enum import Enum

# --- AST Models ---

class ConditionOperators(str, Enum):
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    NOT_EQUAL = "!="
    EQUAL = "="
    WILDCARD = "WILDCARD"
    EXACT = "EXACT"
    
class Condition(BaseModel):
    operator: str
    catalog_value: str
    item_path: Union[str, List[str]] 

class ConditionGroup(BaseModel):
    logic: str  # "AND", "OR", or "SINGLE"
    conditions: List[Condition]

class CatalogQuery(BaseModel):
    catalog_prefix: str  # e.g., "VS", "VT", "VI"
    group: ConditionGroup

class QueryAST(BaseModel):
    version: str
    queries: List[CatalogQuery]

    @staticmethod
    def _standardize_date(date_str: str) -> str:
        """
        Takes a partial date string and pads it to a full ISO-8601 datetime string.
        Defaults missing months to January (01) and missing days to the 1st (01).
        """
        date_str = date_str.strip()
        
        # Match YYYY (e.g., "2020")
        if re.fullmatch(r'\d{4}', date_str):
            return f"{date_str}-01-01T00:00:00Z"
            
        # Match YYYY-MM (e.g., "2020-05")
        elif re.fullmatch(r'\d{4}-\d{2}', date_str):
            return f"{date_str}-01T00:00:00Z"
            
        # Match YYYY-MM-DD (e.g., "2020-05-15")
        elif re.fullmatch(r'\d{4}-\d{2}-\d{2}', date_str):
            return f"{date_str}T00:00:00Z"
            
        # Match full ISO string (return as-is)
        elif "T" in date_str:
            return date_str
            
        # Fallback if they type something completely weird
        return date_str
    
    @staticmethod
    def _parse_single_condition(cond_str: str,prefix:str) -> Condition:
        """Helper to parse an individual condition string."""
        cond_str = cond_str.strip()
        if prefix == "VS":
            catalog_value = "SPATIAL"
        elif prefix == "VT":
            catalog_value = "TEMPORAL"
        else: 
            catalog_value = None


        # 1. Check for math/comparison operators (e.g., > 2000)
        math_match = re.match(r'(>=|<=|>|<|!=|=)\s*(.*)', cond_str)
        if math_match:
            operator = math_match.group(1)
            raw_val = math_match.group(2).strip()
            print("Operator:", operator)
            print("Raw Value:", raw_val)
            if prefix == "VT":
                formmated_val = QueryAST._standardize_date(raw_val)
            else:
                formmated_val = raw_val
            
            return Condition(
                operator      = operator,
                catalog_value = catalog_value,
                item_path     = formmated_val
            )
        # 2. Check for Hierarchy Wildcards (e.g., MX.* or MX.*.*)
        elif '*' in cond_str:
            # Split by dot and remove ALL wildcards to get the root path
            parts = [p for p in cond_str.split('.') if p != '*']
            if prefix == "VI":
                catalog_value = parts[0]  # The first part is the catalog value
                item_path = parts[1:]          # Everything after the first part is the item path
            else:
                item_path = parts  # For VS and VT, the entire path is relevant
            return Condition(operator="WILDCARD", catalog_value=catalog_value, item_path=item_path)
            
        # 3. Exact match / Hierarchy Path (e.g., CIE10.C10)
        else:
            parts = cond_str.split('.')
            if prefix == "VT":
                item_path = QueryAST._standardize_date(cond_str)  
            elif prefix == "VI":
                catalog_value = parts[0]  #
                item_path = parts[1:]  # Everything after the first part is the item path
            else:
                item_path = parts
            # print("Exact Match Item Path:", item_path)
            return Condition(operator="EXACT", catalog_value=catalog_value, item_path=item_path)
    @staticmethod
    def parse(query_str: str) -> "QueryAST":
        """
        Parses a complex Jub query string into an AST with AND/OR logic.
        """
        if not query_str.startswith("jub.v1."):
            raise ValueError("Invalid query format. Must start with 'jub.v1.'")
        
        core_query = query_str[7:]
        
        # Match patterns like VS(...) or VT(...)
        pattern = r'([A-Z]{2})\(([^)]+)\)'
        matches = re.findall(pattern, core_query)
        
        parsed_queries = []
        for prefix, argument in matches:
            argument = argument.strip()
            
            # Determine the logical grouping inside the parentheses
            if ' OR ' in argument:
                logic = "OR"
                raw_conds = argument.split(' OR ')
            elif ' AND ' in argument:
                logic = "AND"
                raw_conds = argument.split(' AND ')
            else:
                logic = "SINGLE"
                raw_conds = [argument]
                
            # Parse each split condition
            conditions = [QueryAST._parse_single_condition(c, prefix) for c in raw_conds]
            
            # Add the logical group to the query list
            group = ConditionGroup(logic=logic, conditions=conditions)
            parsed_queries.append(CatalogQuery(catalog_prefix=prefix, group=group))
            
        return QueryAST(version="v1", queries=parsed_queries)