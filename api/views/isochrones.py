import logging
from typing import Dict
from fastapi import APIRouter, Security
from ..auth import get_api_key
from isochrones import calculate_isochrones, get_osm_features, intersect_isochrones
from ..models.isochrones import IsochronePoisData, IsochroneResponse, FeatureCollection, PoisData
from ..config import config
from ..auth import API_KEYS
from datetime import datetime

router = APIRouter()


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
            data.lat,
            data.lon,
            data.cutoffSec,
            datetime_obj,
            otp_url,
            api_key=api_key,
            router='default',
        )
        if data.categories is None or len(data.categories) == 0:
            return IsochroneResponse(isochrones=isochrones.__geo_interface__, pois=None)

        # Calculate bounding box from isochrones
        if "bbox" in isochrones.__geo_interface__:
            bbox = isochrones.__geo_interface__["bbox"]
        else:
            all_coords = [feature.geometry['coordinates']
                          for feature in isochrones.features]
            lons = [coord[0] for coords in all_coords for coord in (
                coords if isinstance(coords[0], list) else [coords])]
            lats = [coord[1] for coords in all_coords for coord in (
                coords if isinstance(coords[0], list) else [coords])]
            bbox = [min(lons), min(lats), max(lons), max(lats)]

        try:
            # Fetch OSM features within the bounding box
            tags: Dict[str, bool] = {
                category: True for category in data.categories}
            pois = get_osm_features(bbox, tags=tags, crs="EPSG:4326")
            if pois is None or pois.empty:
                return IsochroneResponse(isochrones=isochrones.__geo_interface__, pois=None)

            # Intersect isochrones with POIs
            intersected_pois = intersect_isochrones(isochrones, pois)
            if intersected_pois is None or intersected_pois.empty:
                return IsochroneResponse(isochrones=isochrones.__geo_interface__, pois=None)
        except Exception as e:
            logging.error(e, exc_info=True)
            return IsochroneResponse(isochrones=isochrones.__geo_interface__, pois=None)

        return IsochroneResponse(isochrones=isochrones.__geo_interface__, pois=intersected_pois.__geo_interface__)
    except Exception as e:
        logging.error(e, exc_info=True)
        return IsochroneResponse(isochrones=FeatureCollection(type="FeatureCollection", features=[]), pois=None)


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
