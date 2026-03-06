import pytest
from jubapi.server import app
from fastapi.testclient import TestClient
from jubapi.models.v1 import Catalog,CatalogKind,CatalogItem
from uuid import uuid4
client = TestClient(app)

@pytest.mark.asyncio
async def test_api_create_catalog():
    # Create a new catalog DTO
    catalog = Catalog(
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

            ),
        ]
    )
    response = client.post("/catalogs", json=catalog.model_dump())
    
    print(response.json())
    assert response.status_code == 201, "API request failed"