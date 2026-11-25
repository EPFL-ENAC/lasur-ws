import secrets
from fastapi import HTTPException, status, Security
from fastapi.security import APIKeyHeader
from .config import config

API_KEYS = [key.strip() for key in config.API_KEYS.split(",") if key.strip()]

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


def get_api_key(
    api_key_header: str = Security(api_key_header),
) -> str:
    """Retrieve and validate an API key from the query parameters or HTTP header.

    Args:
        api_key_header: The API key passed in the HTTP header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the API key is invalid or missing.
    """
    # compare bytes: compare_digest rejects non-ASCII str
    if api_key_header and any(
        secrets.compare_digest(api_key_header.encode(), key.encode()) for key in API_KEYS
    ):
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )
