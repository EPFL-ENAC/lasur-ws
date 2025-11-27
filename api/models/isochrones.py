from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


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
        None, description="Source of POI data (e.g., 'osm.pbf')")
    cached: Optional[bool] = Field(
        False, description="Whether to use cached POI data if available")


class IsochronePoisData(IsochroneData):
    categories: Optional[List[str]] = Field(
        None, description="List of POI categories to filter")
    overlap: Optional[bool] = Field(
        True, description="Whether to return overlapping isochrones or non-overlapping ones")


class IsochroneResponse(BaseModel):
    isochrones: FeatureCollection
    pois: Optional[FeatureCollection] = None
