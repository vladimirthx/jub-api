import pytest

from dotenv import load_dotenv
import os

JUB_ENV_FILE_PATH = os.environ.get("JUB_ENV_FILE_PATH", ".env.test")
os.environ.setdefault("JUB_ENV_FILE_PATH", JUB_ENV_FILE_PATH)
env_exists        = os.path.exists(JUB_ENV_FILE_PATH)

print(f"Loading environment variables from: {JUB_ENV_FILE_PATH} - Exists: {env_exists}")
if env_exists:
    load_dotenv(JUB_ENV_FILE_PATH, override=True)



async def connect_to_database():
    from jubapi.db import connect_to_mongo
    print("Connecting to the database...")
    await connect_to_mongo()
    # await asyncio.sleep(0.1)  # simulate async connection

@pytest.fixture( autouse=True)
async def before_all():
    from jubapi.db import close_mongo_connection
    await connect_to_database()
    print("Database connected before tests")
    yield 
    print("Disconnecting from database...")
    await close_mongo_connection()