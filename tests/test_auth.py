import os

import pytest
from fastapi import HTTPException

os.environ.setdefault("API_KEYS", "test")
from api import auth  # noqa: E402


def test_get_api_key(monkeypatch):
    monkeypatch.setattr(auth, "API_KEYS", ["first", "second"])
    assert auth.get_api_key("first") == "first"
    assert auth.get_api_key("second") == "second"
    for key in (None, "", "firs", "first,second", "clé"):
        with pytest.raises(HTTPException) as e:
            auth.get_api_key(key)
        assert e.value.status_code == 401
