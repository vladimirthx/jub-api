import os
from motor.motor_asyncio import AsyncIOMotorClient,AsyncIOMotorCollection
import jubapi.config as CX


client              = None

# Get the MongoDB client and database instance
def get_database():
    global client
    return  client[CX.JUB_MONGODB_DATABASE_NAME] if client else None 

def get_collection(name:str)->AsyncIOMotorCollection:
    db =  get_database()
    return db[name] if not db is None else None 
# Startup event to initialize the MongoClient when the application starts
async def connect_to_mongo():
    global client
    client = AsyncIOMotorClient(CX.JUB_MONGODB_URI)
    print(f"MongoDB connection established. URI: {CX.JUB_MONGODB_URI}")

# Shutdown event to close the MongoClient when the application shuts down
async def close_mongo_connection():
    global client
    client.close()