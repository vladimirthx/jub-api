import pytest
from fastapi.testclient import TestClient
from jubapi.server import app
from jubapi.models.v1 import Product
from uuid import uuid4


client = TestClient(app)

@pytest.fixture
def prod():
    """Fixture to provide a standard valid product payload."""
    return Product(
        pid=uuid4().hex[:6],
        description="A tested product",
        level_path="/some/path",
        levels=[],
        product_name="TESTED PRODUCT",
        product_type="Some type",
        profile="public",
        tags=["Tested"],
        url="http://example.com/data",

    )



# Operation of Create
@pytest.mark.asyncio
async def test_create_multiple_products(prod):
    """Validates the batch insertion endpoint using a List of Product models."""
    # The endpoint expects a List[ProductDTO]
    payload = [prod.model_dump()]
    response = client.post("/products", json=payload)
    
    # 201 Created and response_model=None means empty content
    assert response.status_code == 201
    assert response.content == b''

# Operation of Read
@pytest.mark.asyncio
async def test_get_products():
    """Test fetching products with pagination."""
    response = client.get("/products")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Operation of Delete
@pytest.mark.asyncio
async def test_delete_product(prod):
    """Test deleting a product by its PID."""
    response = client.delete(f"/products/{prod.pid}")
    assert response.status_code in [204, 404]

# Negative Test
@pytest.mark.asyncio
async def test_create_products_invalid_payload():
    """NEGATIVE TEST: Submits a dict instead of the required List[Product]."""
    # Endpoint expects List[ProductDTO], instead a dict is sended
    invalid_payload = {"pid": "123", "product_name": "Bad Payload"}
    
    response = client.post("/products", json=invalid_payload)
    # Should trigger a 422 Unprocessable Entity due to strict type checking
    assert response.status_code == 422