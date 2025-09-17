import logging
from typing import Dict
from fastapi import APIRouter, Security
from ..auth import get_api_key
from isochrones import calculate_isochrones, get_osm_features
from ..models.isochrones import IsochroneData, FeatureCollection, PoisData
from ..config import config
from ..auth import API_KEYS
from datetime import datetime

router = APIRouter()


@router.post("/compute", response_model=FeatureCollection, response_model_exclude_none=True)
async def compute_isochrones(
    data: IsochroneData,
    api_key: str = Security(get_api_key),
) -> FeatureCollection:
    """Compute isochrones based on the provided data."""
    otp_url = config.OTP_URL
    # Use the first API key if available
    api_key = API_KEYS[0] if API_KEYS else None
    # parse datetime in ISO 8601 format into an object
    datetime_obj = datetime.fromisoformat(data.datetime)
    try:
        isochrones = calculate_isochrones(
            data.lat,
            data.lon,
            data.cutoffSec,
            datetime_obj,
            otp_url,
            api_key=api_key,
            router='default',
        )
        return isochrones.__geo_interface__
    except Exception as e:
        logging.error(e, exc_info=True)
        return {'error': str(e)}


@router.post("/pois", response_model=FeatureCollection, response_model_exclude_none=True)
async def get_pois(
    data: PoisData,
    api_key: str = Security(get_api_key),
) -> FeatureCollection:
    """Get available OSM features for isochrone calculations."""
    tags = {}
    for category in data.categories or []:
        tags[category] = True
    try:
        features = get_osm_features(data.bbox, tags=tags, crs="EPSG:4326")
        return features.__geo_interface__
    except Exception as e:
        logging.error(e, exc_info=True)
        return FeatureCollection(type="FeatureCollection", features=[], bbox=data.bbox)
