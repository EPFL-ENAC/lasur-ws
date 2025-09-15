from fastapi import APIRouter, Response, Security
from ..auth import get_api_key

router = APIRouter()


@router.get("", response_class=Response)
async def auth(
    api_key: str = Security(get_api_key),
) -> Response:
    """Verify authentication."""
    return Response(status_code=200)
