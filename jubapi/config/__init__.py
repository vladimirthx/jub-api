from dotenv import load_dotenv
import os
JUB_ENV_FILE_PATH = os.environ.get("JUB_ENV_FILE_PATH",".env")
jub_env_exists = os.path.exists(JUB_ENV_FILE_PATH)
print(f"Loading environment variables from: {JUB_ENV_FILE_PATH} - Exists: {jub_env_exists}")
if jub_env_exists:
    load_dotenv(JUB_ENV_FILE_PATH,override=True)

JUB_MONGODB_URI           = os.environ.get("JUB_MONGODB_URI","mongodb://localhost:27017/jub")
JUB_MONGODB_DATABASE_NAME = os.environ.get("JUB_MONGODB_DATABASE_NAME","jub")
JUB_OPENAPI_TITLE         = os.environ.get("JUB_OPENAPI_TITLE","OCA - API")
JUB_OPENAPI_VERSION       = os.environ.get("JUB_OPENAPI_VERSION","0.0.1")
JUB_OPENAPI_SUMMARY       = os.environ.get("JUB_OPENAPI_SUMMARY","This API enable the manipulation of observatories and catalogs")
JUB_OPENAPI_DESCRIPTION   = os.environ.get("JUB_OPENAPI_DESCRIPTION","")
JUB_OPENAPI_LOGO          = os.environ.get("JUB_OPENAPI_LOGO","https://i.ibb.co/9vSnz09/android-chrome-192x192.png")
JUB_OPENAPI_PREFIX        = os.environ.get("JUB_OPENAPI_PREFIX","")
JUB_LOG_DEBUG             = bool(int(os.environ.get("JUB_LOG_DEBUG","1")))
JUB_LOG_NAME              = os.environ.get("JUB_LOG_NAME","jubapi")
JUB_LOG_PATH              = os.environ.get("JUB_LOG_PATH","/log")
JUB_CORS_ORIGINS     = os.getenv("JUBAPI_CORS_ORIGINS","*").split(",")
JUB_CORS_METHODS     = os.getenv("JUBAPI_CORS_METHODS","*").split(",")
JUB_CORS_HEADERS     = os.getenv("JUBAPI_CORS_HEADERS","*").split(",")
JUB_CORS_CREDENTIALS = os.getenv("JUBAPI_CORS_CREDENTIALS","True").lower() in ("true", "1")
