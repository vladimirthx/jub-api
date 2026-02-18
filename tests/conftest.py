import asyncio
import pytest

from jubapi.db import connect_to_mongo,close_mongo_connection
from dotenv import load_dotenv
import os

ENV_FILE_PATH = os.environ.get("ENV_FILE_PATH", ".env.test")
if os.path.exists(ENV_FILE_PATH):
    load_dotenv(ENV_FILE_PATH)



async def connect_to_database():
    print("Connecting to the database...")
    await connect_to_mongo()
    # await asyncio.sleep(0.1)  # simulate async connection

@pytest.fixture( autouse=True)
async def before_all(event_loop):
    await connect_to_database()
    print("Database connected before tests")
    yield 
    print("Disconnecting from database...")
    await close_mongo_connection()