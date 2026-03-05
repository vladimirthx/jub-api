import pytest
from pydantic import ValidationError

# Assuming the models are saved in a file named `models.py`
from jubapi.models.v2 import CatalogX, CatalogType
# Assuming the parser is saved in a file named `parser.py`
from jubapi.querylang.v4.parser import QueryAST

def test_upper_snake_str_validation():
    """
    Tests that the custom Pydantic validator correctly transforms 
    messy inputs into clean UPPER_SNAKE_CASE.
    """
    # Create a dummy catalog to trigger the validation
    catalog = CatalogX(
        catalog_id   = "cat_01",
        name         = "Test Catalog",
        value        = "camelCase value-with-hyphens",
        catalog_type = CatalogType.INTEREST,
        description  = "A test catalog",
        metadata     = None
    )
    
    # Assert that the validator intercepted and formatted the string
    assert catalog.value == "CAMEL_CASE_VALUE_WITH_HYPHENS"

def test_ast_parser_valid_query():
    """
    Tests that the parser correctly builds the AST for a complex Jub query.
    """
    query_str = "jub.v1.VS(MX.SLP.*).VT(>=2000).VI(SEX.MALE)"
    ast = QueryAST.parse(query_str)
    
    assert isinstance(ast, QueryAST)
    assert ast.version == "v1"
    assert len(ast.queries) == 3

    assert ast.queries[0].catalog_prefix == "VS"
    assert ast.queries[0].group.logic == "SINGLE"
    assert ast.queries[0].group.conditions[0].operator == "WILDCARD"
    assert ast.queries[0].group.conditions[0].catalog_value == "SPATIAL"
    assert ast.queries[0].group.conditions[0].item_path == ["MX", "SLP"]

    assert ast.queries[1].catalog_prefix == "VT"
    assert ast.queries[1].group.logic == "SINGLE"
    assert ast.queries[1].group.conditions[0].operator == ">="
    assert ast.queries[1].group.conditions[0].catalog_value == "TEMPORAL"
    assert ast.queries[1].group.conditions[0].item_path == "2000-01-01T00:00:00Z"  # Padded to full date

    
def test_ast_parser_invalid_prefix():
    """
    Tests that the parser rejects invalid query formats.
    """
    with pytest.raises(ValueError, match="Invalid query format"):
        QueryAST.parse("invalid.query.VS(MX)")

def test_ast_parser_explicit_catalogs():
    """
    Tests that the AST correctly assigns implicit catalogs (SPATIAL/TEMPORAL)
    and extracts explicit catalogs (INTEREST) based on the variable type.
    """
    query_str = "jub.v1.VS(MX.*.* AND USA.*.*).VT(> 2000 AND <2020).VI(CIE10.C10 OR SEX.MALE)"
    ast = QueryAST.parse(query_str)
    
    # 1. Verify Spatial (VS) assigns SPATIAL automatically
    vs_query = ast.queries[0]
    assert vs_query.group.logic == "AND"
    
    cond_mx = vs_query.group.conditions[0]
    assert cond_mx.catalog_value == "SPATIAL"
    assert cond_mx.item_path == ["MX"]
    
    cond_usa = vs_query.group.conditions[1]
    assert cond_usa.catalog_value == "SPATIAL"
    assert cond_usa.item_path == ["USA"]
    
    # 2. Verify Temporal (VT) assigns TEMPORAL automatically
    vt_query = ast.queries[1]
    assert vt_query.group.logic == "AND"
    
    cond_gt = vt_query.group.conditions[0]
    assert cond_gt.catalog_value == "TEMPORAL"
    assert cond_gt.operator == ">"
    assert cond_gt.item_path == "2000-01-01T00:00:00Z"  # Padded to full date
    
    # 3. Verify Interest (VI) extracts the catalog dynamically from the string
    vi_query = ast.queries[2]
    assert vi_query.group.logic == "OR"
    
    cond_cie10 = vi_query.group.conditions[0]
    assert cond_cie10.catalog_value == "CIE10" # Extracted!
    assert cond_cie10.item_path == ["C10"]     # Separated from catalog!
    
    cond_sex = vi_query.group.conditions[1]
    assert cond_sex.catalog_value == "SEX"     # Extracted!
    assert cond_sex.item_path == ["MALE"]      # Separated from catalog!


def test_ast_parser_temporal_date_padding():
    """
    Tests that the VT catalog correctly identifies partial dates 
    (Year, Year-Month) and pads them to full ISO-8601 strings.
    """
    # Query testing a pure year, a year-month, and an exact date
    query_str = "jub.v1.VT(> 2020 AND <= 2023-05).VT(2025-10-31)"
    ast = QueryAST.parse(query_str)
    
    # 1. Verify the '2020' was padded to Jan 1st
    vt_group_1 = ast.queries[0].group
    cond_gt_2020 = vt_group_1.conditions[0]
    assert cond_gt_2020.operator == ">"
    assert cond_gt_2020.item_path == "2020-01-01T00:00:00Z"
    
    # 2. Verify the '2023-05' was padded to the 1st of May
    cond_lte_2023 = vt_group_1.conditions[1]
    assert cond_lte_2023.operator == "<="
    assert cond_lte_2023.item_path == "2023-05-01T00:00:00Z"
    
    # 3. Verify the exact match '2025-10-31' appended the correct time
    vt_group_2 = ast.queries[1].group
    cond_exact = vt_group_2.conditions[0]
    assert cond_exact.operator == "EXACT"
    assert cond_exact.item_path == "2025-10-31T00:00:00Z"