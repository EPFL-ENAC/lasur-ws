from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class IsochroneData(BaseModel):
    lon: float
    lat: float
    cutoffSec: List[int]
    datetime: str  # ISO 8601 format


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
