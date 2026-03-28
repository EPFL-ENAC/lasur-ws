import logging
from typing import Dict
from datetime import datetime
import geopandas as gpd
from fastapi import APIRouter, Security

from isochrones import calculate_isochrones, get_available_modes

from ..utils.isochrones import get_pois_within_isochrones
from ..auth import get_api_key
from ..service.pois import PoisService
from ..models.isochrones import IsochronePoisData, IsochroneResponse, FeatureCollection, PoisData
from ..config import config
from ..auth import API_KEYS

router = APIRouter()


@router.get("/modes", response_model=Dict[str, str], response_model_exclude_none=True)
async def get_modes(api_key: str = Security(get_api_key)) -> Dict[str, str]:
    otp_url = config.OTP_URL
    # Use the first API key if available
    api_key = API_KEYS[0] if API_KEYS else None
    available_modes = get_available_modes(otp_url, api_key=api_key)
    return available_modes


@router.post("/compute", response_model=IsochroneResponse, response_model_exclude_none=True)
async def compute_isochrones(
    data: IsochronePoisData,
    api_key: str = Security(get_api_key),
) -> IsochroneResponse:
    """Compute isochrones and points of interest based on the provided data."""
    otp_url = config.OTP_URL
    # Use the first API key if available
    api_key = API_KEYS[0] if API_KEYS else None
    # parse datetime in ISO 8601 format into an object
    datetime_obj = datetime.fromisoformat(data.datetime)
    try:
        isochrones = calculate_isochrones(
            lat=data.lat,
            lon=data.lon,
            cutoffSec=data.cutoffSec,
            date_time=datetime_obj,
            mode=data.mode if hasattr(data, 'mode') else 'WALK',
            otp_url=otp_url,
            api_key=api_key,
            bike_speed=data.bikeSpeed if hasattr(data, 'bikeSpeed') else 13.0,
            router=data.router if hasattr(data, 'router') else 'default',
            overlap=data.overlap,
        )
        if data.categories is None or len(data.categories) == 0:
            return IsochroneResponse(isochrones=isochrones.__geo_interface__, pois=None)

        # Calculate bounding box from isochrones
        """ if "bbox" in isochrones.__geo_interface__:
            bbox = isochrones.__geo_interface__["bbox"]
        else:
            all_coords = [feature.geometry['coordinates']
                          for feature in isochrones.features]
            lons = [coord[0] for coords in all_coords for coord in (
                coords if isinstance(coords[0], list) else [coords])]
            lats = [coord[1] for coords in all_coords for coord in (
                coords if isinstance(coords[0], list) else [coords])]
            bbox = [min(lons), min(lats), max(lons), max(lats)] """
        
        try:
            # Fetch OSM features within the bounding box
            # tags: Dict[str, bool] = { category: True for category in data.categories } // Doesn't seem to be used, can this be removed?

            pois_service = PoisService()

            pois_within = await get_pois_within_isochrones(isochrones, data.categories, pois_service)
            if pois_within is None:
                return IsochroneResponse(isochrones=isochrones.__geo_interface__, pois=None)
            
        except Exception as e:
            logging.error(e, exc_info=True)
            return IsochroneResponse(isochrones=isochrones.__geo_interface__, pois=None)

        # TODO : cache this response in redis for 1-24 hours so that we can make the platyp admin load the recurrent ones faster ?
        return IsochroneResponse(isochrones=isochrones.__geo_interface__, pois=pois_within.__geo_interface__)
    except Exception as e:
        logging.error(e, exc_info=True)
        return IsochroneResponse(isochrones=FeatureCollection(type="FeatureCollection", features=[]), pois=None)


@router.post("/pois", response_model=FeatureCollection, response_model_exclude_none=True)
async def get_pois(
    data: PoisData,
    api_key: str = Security(get_api_key),
) -> FeatureCollection:
    """Get available OSM features for isochrone calculations."""
    try:
        pois_service = PoisService()
        features = await pois_service.get_pois(
            bbox=data.bbox,
            categories=data.categories,
            source=data.source,
            cached=data.cached
        )
        return features
    except Exception as e:
        logging.error(e, exc_info=True)
        return FeatureCollection(type="FeatureCollection", features=[], bbox=data.bbox)


@router.post("/pois/_cache", response_model=Dict, response_model_exclude_none=True)
async def get_pois(
    api_key: str = Security(get_api_key),
) -> Dict:
    """Get available OSM features for isochrone calculations and cache them.
    Use default bounding box and categories from config.
    """
    try:
        pois_service = PoisService()
        count_by_category = await pois_service.make_cache()
        return count_by_category
    except Exception as e:
        logging.error(e, exc_info=True)
        return {'error': str(e)}


@router.delete("/pois/_cache", response_model=None)
async def delete_pois_cache(
    api_key: str = Security(get_api_key),
) -> None:
    """Delete all cached OSM features."""
    try:
        pois_service = PoisService()
        await pois_service.delete_cache()
    except Exception as e:
        logging.error(e, exc_info=True)
        return None
