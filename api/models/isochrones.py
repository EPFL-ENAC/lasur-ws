from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

# Max bbox side in degrees (~150x220 km): covers a 60 min transit isochrone, bounds the spatial query cost
MAX_BBOX_SPAN = 2.0


class IsochroneData(BaseModel):
    lon: float
    lat: float
    cutoffSec: List[int]
    datetime: str  # ISO 8601 format
    mode: Optional[str] = "WALK"  # e.g., "WALK", "BICYCLE", "TRANSIT"
    bikeSpeed: Optional[float] = None
    router: Optional[str] = "default"


class FeatureGeometry(BaseModel):
    type: str
    coordinates: Any


class Feature(BaseModel):
    id: str
    type: str
    geometry: FeatureGeometry
    properties: Dict[str, Any]
    bbox: Optional[List[float]] = None


class FeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[Feature]
    bbox: Optional[List[float]] = None


class PoisData(BaseModel):
    bbox: List[float] = Field(...,
                              description="Bounding box [minLon, minLat, maxLon, maxLat]")
    categories: Optional[List[str]] = Field(
        None, description="List of POI categories to filter")
    source: Optional[str] = Field(
        None, pattern=r"^[A-Za-z0-9_-]+$", description="Source area of POI data (e.g., 'geneva')")
    cached: Optional[bool] = Field(
        False, description="Whether to use cached POI data if available")

    @field_validator("bbox")
    @classmethod
    def check_bbox(cls, bbox: List[float]) -> List[float]:
        if len(bbox) != 4:
            raise ValueError("bbox must be [minLon, minLat, maxLon, maxLat]")
        min_lon, min_lat, max_lon, max_lat = bbox
        if not (-180 <= min_lon < max_lon <= 180 and -90 <= min_lat < max_lat <= 90):
            raise ValueError("bbox coordinates out of range or inverted")
        if max_lon - min_lon > MAX_BBOX_SPAN or max_lat - min_lat > MAX_BBOX_SPAN:
            raise ValueError(f"bbox sides must not exceed {MAX_BBOX_SPAN} degrees")
        return bbox


class IsochronePoisData(IsochroneData):
    categories: Optional[List[str]] = Field(
        None, description="List of POI categories to filter")
    overlap: Optional[bool] = Field(
        True, description="Whether to return overlapping isochrones or non-overlapping ones")


class IsochroneResponse(BaseModel):
    isochrones: FeatureCollection
    pois: Optional[FeatureCollection] = None
    transit: Optional[FeatureCollection] = None
