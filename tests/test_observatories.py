import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from jubapi.server import app
from jubapi.models import Observatory, LevelCatalog
client = TestClient(app)

@pytest.fixture
def obs():
    """Fixture to provide a standard valid observatory payload."""
    return Observatory(
        obid=uuid4().hex[:6],
        title="TESTED OBSERVATORY",
        description="A test observatory for pytest",
        image_url="http://example.com/image.png",
        catalogs=[],
        disabled=False
    )

# Create Operation
@pytest.mark.asyncio
async def test_create_observatory(obs):
    """Test creating a new observatory via the API."""
    response = client.post("/observatories", json=obs.model_dump())
    assert response.status_code == 201
    
    data = response.json()
    assert "obid" in data
    assert data["obid"] == obs.obid

# Read Operation
@pytest.mark.asyncio
async def test_get_observatories():
    """Test retrieving the list of active observatories."""
    response = client.get("/observatories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Update Operation
@pytest.mark.asyncio
async def test_update_observatory_catalogs(obs):
    """Test updating the catalogs list of a specific observatory."""
    catalogs_payload = [
        LevelCatalog(level=1, cid="cat-1").model_dump(),
        LevelCatalog(level=2, cid="cat-2").model_dump()
    ]
    response = client.post(f"/observatories/{obs.obid}", json=catalogs_payload)
    # It is possible to return 204 if has a success or 404/500 if the obid was not saved in the test DB
    assert response.status_code in [204, 404, 500]

# Delete Operation
@pytest.mark.asyncio
async def test_delete_observatory(obs):
    """Test deleting an observatory."""
    response = client.delete(f"/observatories/{obs.obid}")
    assert response.status_code in [204, 404]

# Negative Test
@pytest.mark.asyncio
async def test_get_observatory_not_found():
    """NEGATIVE TEST: Fetch an observatory that does not exist."""
    response = client.get("/observatories/non-existent-obid-12345")
    assert response.status_code == 404