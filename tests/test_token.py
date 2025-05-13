import time

import pytest

from wnm_sharepoint_client.client import SharePointClient
from wnm_sharepoint_client.auth import TokenManager

@pytest.fixture(scope="module")
def client():
    return SharePointClient("HORTA")

def test_token_refresh_logic(monkeypatch):
    "This test should be the last test run or put in a separate test file"

    tm = TokenManager()
    # Expire the token
    tm.expiry = time.time() - 1

    # Force refresh
    monkeypatch.setattr(
        "requests.post",
        lambda *a, **kw: type(
            "MockResp",
            (),
            {
                "raise_for_status": lambda self: None,
                "json": lambda self: {
                    "access_token": "new-token",
                    "expires_in": 3600,
                },
            },
        )(),
    )

    new_token = tm.get_token()
    assert new_token == "new-token"
