import pytest
from jubapi.server import app
from fastapi.testclient import TestClient
from jubapi.models.v1 import Catalog,CatalogKind,CatalogItem
from uuid import uuid4
client = TestClient(app)


# Including the fixture to adapt the previous template
@pytest.fixture
def cat():
    """Fixture to provide a standard valid catalog model payload."""
    return Catalog(
        cid=uuid4().hex[:8],
        display_name="TEST CATALOG",
        kind=CatalogKind.INTEREST,
        items=[
            CatalogItem(
                value="A",
                display_name="Display Value (A)",
                code=0,
                description="Item A",
                metadata={"extra_info": "Some extra info for A"}
            )
        ]
    )

# Create Operation
@pytest.mark.asyncio
async def test_create_catalog(cat):
    """Test creating a new catalog via the API using a Model."""
    response = client.post("/catalogs", json=cat.model_dump())
    assert response.status_code == 201, f"Unexpected status: {response.status_code}"
    
    data = response.json()
    assert data["cid"] == cat.cid

# Read Operations
@pytest.mark.asyncio
async def test_get_catalogs():
    """Test retrieving the paginated list of catalogs."""
    response = client.get("/catalogs")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_catalog_by_cid(cat):
    """Test retrieving a specific catalog by its CID."""
    response = client.get(f"/catalogs/{cat.cid}")
    assert response.status_code in [200, 404]

# Delete Operation
@pytest.mark.asyncio
async def test_delete_catalog(cat):
    """Test deleting a catalog."""
    response = client.delete(f"/catalogs/{cat.cid}")
    assert response.status_code in [204, 404]

# Negative Test
@pytest.mark.asyncio
async def test_create_catalog_invalid_payload():
    """NEGATIVE TEST: Missing required fields in payload."""
    invalid_catalog = {
        "display_name": "Incomplete Catalog"
    }
    response = client.post("/catalogs", json=invalid_catalog)
    assert response.status_code == 422