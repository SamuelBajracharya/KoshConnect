import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10080

# Security hardening toggles
ENFORCE_HTTPS = os.getenv("ENFORCE_HTTPS", "false").lower() == "true"
APP_ENV = os.getenv("APP_ENV", "development").lower()

# Key management settings for sandbox envelope encryption.
MASTER_KEY_B64 = os.getenv("MASTER_KEY_B64")
STRICT_KEY_MANAGEMENT = os.getenv("STRICT_KEY_MANAGEMENT", "false").lower() == "true"
