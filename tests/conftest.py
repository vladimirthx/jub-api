import asyncio
import pytest

from jubapi.db import connect_to_mongo,close_mongo_connection
from dotenv import load_dotenv
import os

JUB_ENV_FILE_PATH = os.environ.get("JUB_ENV_FILE_PATH", ".env.test")
env_exists        = os.path.exists(JUB_ENV_FILE_PATH)

print(f"Loading environment variables from: {JUB_ENV_FILE_PATH} - Exists: {env_exists}")
if env_exists:
    load_dotenv(JUB_ENV_FILE_PATH, override=True)



async def connect_to_database():
    print("Connecting to the database...")
    await connect_to_mongo()
    # await asyncio.sleep(0.1)  # simulate async connection

@pytest.fixture( autouse=True)
async def before_all():
    await connect_to_database()
    print("Database connected before tests")
    yield 
    print("Disconnecting from database...")
    await close_mongo_connection()