import threading
import time

import requests

from .config import CLIENT_ID, CLIENT_SECRET, SCOPE, TENANT_ID
from .logger import logger


class SingletonMeta(type):
    _instances = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class TokenManager(metaclass=SingletonMeta):
    def __init__(self):
        self.token = None
        self.expiry = 0
        self._lock = threading.Lock()

    def get_token(self) -> str:
        with self._lock:
            if not self.token or time.time() >= self.expiry:
                self.refresh_token()
            return self.token

    def refresh_token(self):
        logger.info("Refreshing token...")
        token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": SCOPE,
        }
        response = requests.post(token_url, data=data, timeout=10)
        response.raise_for_status()
        token_data = response.json()
        self.token = token_data["access_token"]
        self.expiry = (
            time.time() + int(token_data.get("expires_in", 3600)) - 60
        )  # Refresh 1 min before expiry

    def get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json",
        }


token_manager = TokenManager()
