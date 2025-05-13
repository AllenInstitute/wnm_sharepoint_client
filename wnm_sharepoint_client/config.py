import os
from dotenv import load_dotenv
import warnings

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

# Optionally load .env file if DOTENV_PATH is specified
dotenv_path = os.getenv("DOTENV_PATH")
if dotenv_path:
    if not os.path.isfile(dotenv_path):
        raise ConfigError(f"DOTENV_PATH is set but file does not exist: {dotenv_path}")
    
    vars_loaded = load_dotenv(dotenv_path=dotenv_path)
    if not vars_loaded:
        raise ConfigError(f".env file at {dotenv_path} was found but no variables were loaded.")
else:
    warning_msg = "DOTENV_PATH is not set. Will try to load variables directly from environment."
    warnings.warn(warning_msg, UserWarning)
    # Not an error - manual env setup is allowed
    pass

required_env_vars = [
    "TENANT_ID",
    "CLIENT_ID",
    "CLIENT_SECRET",
    "SITE_ID",
    "DRIVE_ID",
    "SCOPE"
]

missing_vars = [var for var in required_env_vars if os.getenv(var) is None]
if missing_vars:
    msg = "Missing required environment variables:\n" + "\n".join(missing_vars)
    msg = msg
    raise ConfigError(msg)

# Load variables after validation
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SITE_ID = os.getenv("SITE_ID")
DRIVE_ID = os.getenv("DRIVE_ID")
SCOPE = os.getenv("SCOPE") 
GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"
