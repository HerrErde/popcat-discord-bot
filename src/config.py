import os
from dotenv import load_dotenv

load_dotenv()

VERSION = "1.0.0"

TOKEN = os.getenv("TOKEN", "")
DEBUG = bool(os.getenv("DEBUG", False))
TIMEZONE = os.getenv("TIMEZONE", "Europe/Berlin")
API_URL = os.getenv("API_URL", "https://popcat-api.herrerde.xyz")

SHARDING = bool(os.getenv("SHARDING", False))
AUTO_SHARDING = bool(os.getenv("AUTO_SHARDING", True))

WELCOME_URL = os.getenv("WELCOME_URL", None)


OWNER_USER_IDS = os.getenv("OWNER_USER_IDS")
if OWNER_USER_IDS:
    OWNER_USER_IDS = [int(id_str) for id_str in OWNER_USER_IDS.split(",")]

OWNER_GUILD_IDS = os.getenv("OWNER_GUILD_IDS")
if OWNER_GUILD_IDS:
    OWNER_GUILD_IDS = [int(id_str) for id_str in OWNER_GUILD_IDS.split(",")]

REPORT_CHANNEL = int(os.getenv("REPORT_CHANNEL", 0))


# Database configuration
MONGODB_URI = os.getenv("MONGODB_URI")

# If MONGODB_URI is not set, construct it using other environment variables
if MONGODB_URI is None:
    # Retrieve other necessary environment variables
    DB_HOST = os.getenv("MONGODB_HOST")
    DB_USER = os.getenv("MONGODB_USER")
    DB_PASS = os.getenv("MONGODB_PASS")
    DB_CLUSTER = os.getenv("MONGODB_CLUSTER")

    # Construct the MongoDB URI
    MONGODB_URI = f"mongodb+srv://{DB_USER}:{DB_PASS}@{DB_HOST}/?retryWrites=true&w=majority&appName={DB_CLUSTER}"

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_DB = os.getenv("REDIS_DB", "")
REDIS_USER = os.getenv("REDIS_USER", "")
REDIS_PASS = os.getenv("REDIS_PASS", "")

REQ_CACHE_BACK = bool(os.getenv("REQ_CACHE_BACK", "sqlite"))
REQ_CACHE_PATH = bool(os.getenv("REQ_CACHE_PATH", "cache/http.sqlite"))
REQ_CACHE_EXP = bool(os.getenv("REQ_CACHE_EXP", 86400))


VOTING_ENABLE = bool(os.getenv("VOTING_ENABLE", True))
VOTING_DELAY = int(os.getenv("VOTING_DELAY", 10))
VOTING_HOOK = bool(os.getenv("VOTING_HOOK", False))
VOTING_KEY = str(os.getenv("VOTING_KEY", ""))
VOTING_PORT = os.getenv("VOTING_PORT", 0)


CHATBOT_ENABLE = bool(os.getenv("CHATBOT_ENABLE", True))
BRAINSHOP_APIKEY = str(os.getenv("BRAINSHOP_APIKEY", ""))
BRAINSHOP_ID = str(os.getenv("BRAINSHOP_ID", ""))


TODO_WEB = bool(os.getenv("TODO_WEB", False))
TODO_WEB_PORT = os.getenv("TODO_WEB_PORT", 80)
OAUTH2_CLIENT_ID = str(os.getenv("OAUTH2_CLIENT_ID", ""))
OAUTH2_CLIENT_SECRET = str(os.getenv("OAUTH2_CLIENT_SECRET", ""))
FLASK_SECRET_KEY = str(os.getenv("FLASK_SECRET_KEY", ""))
OAUTH2_REDIRECT_URI = str(os.getenv("OAUTH2_REDIRECT_URI", ""))
