import os

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.getenv("DOTENV_PATH", ".env"))

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SITE_ID = os.getenv("SITE_ID")
DRIVE_ID = os.getenv("DRIVE_ID")
SCOPE = os.getenv("SCOPE", "https://graph.microsoft.com/.default")

GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"
