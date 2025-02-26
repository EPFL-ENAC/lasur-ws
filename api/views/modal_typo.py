from typing import Dict
from fastapi import APIRouter, Security
from ..auth import get_api_key
from typo_modal.service import TypoModalService, load_data

router = APIRouter()

od_mm, orig_dess, dest_dess = load_data()

@router.get("/geo", response_model=Dict)
async def compute_geo(
    o_lon: float, o_lat: float, d_lon: float, d_lat: float,
    api_key: str = Security(get_api_key),
) -> Dict:
    """Compute modal typology based on the provided data."""
    service = TypoModalService(od_mm, orig_dess, dest_dess)
    try:
        return service.compute_geo(o_lon, o_lat, d_lon, d_lat)
    except Exception as e:
        return {'error': str(e)}
