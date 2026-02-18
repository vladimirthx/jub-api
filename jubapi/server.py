import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from jubapi.log.log import Log
from jubapi.db import connect_to_mongo,close_mongo_connection
from jubapi.controllers import observatories_router,catalogs_router,products_router,v3_router
from jubapi.controllers.v2 import observatory_router_v2,xvariable_router,nameservice_router,product_router_v2
import jubapi.config as CX
from dotenv import load_dotenv

JUB_ENV_PATH = os.getenv("JUBAPI_ENV_PATH","./.env")
if os.path.exists(JUB_ENV_PATH):
    load_dotenv(JUB_ENV_PATH)

log       = Log(
    name                   = CX.JUB_LOG_NAME,  
    path                   = CX.JUB_LOG_PATH,
    console_handler_filter = lambda x : CX.JUB_LOG_DEBUG,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield 
    await close_mongo_connection()

    
app = FastAPI(
    lifespan  = lifespan,
    root_path = CX.JUB_OPENAPI_PREFIX,
    title     = CX.JUB_OPENAPI_TITLE,
)

JUB_CORS_ORIGINS     = os.getenv("JUBAPI_CORS_ORIGINS","*").split(",")
JUB_CORS_METHODS     = os.getenv("JUBAPI_CORS_METHODS","*").split(",")
JUB_CORS_HEADERS     = os.getenv("JUBAPI_CORS_HEADERS","*").split(",")
JUB_CORS_CREDENTIALS = os.getenv("JUBAPI_CORS_CREDENTIALS","True").lower() in ("true", "1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=JUB_CORS_ORIGINS,
    allow_credentials=JUB_CORS_CREDENTIALS,
    allow_methods=JUB_CORS_METHODS,
    allow_headers=JUB_CORS_HEADERS
)
def generate_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title       = CX.JUB_OPENAPI_TITLE,
        version     = CX.JUB_OPENAPI_VERSION,
        summary     = CX.JUB_OPENAPI_VERSION,
        description = CX.JUB_OPENAPI_DESCRIPTION,
        routes      = app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url":  CX.JUB_OPENAPI_LOGO
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema
app.openapi = generate_openapi

app.include_router(observatories_router)
app.include_router(catalogs_router)
app.include_router(products_router)
app.include_router(observatory_router_v2)
app.include_router(xvariable_router)
app.include_router(nameservice_router)
app.include_router(product_router_v2)
app.include_router(v3_router)