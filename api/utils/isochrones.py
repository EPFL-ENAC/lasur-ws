import geopandas as gpd
from isochrones import intersect_isochrones

from ..service.pois import PoisService

# TODO : this should probably be moved to the isochrones package itself
def get_isochrones_bbox(isochrones: gpd.GeoDataFrame) -> list[float]:
        """Calculate the bounding box of the isochrones GeoDataFrame."""
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
        
        return bbox


async def get_pois_within_isochrones(isochrones: gpd.GeoDataFrame, categories: list[str], pois_service: PoisService | None = None) -> gpd.GeoDataFrame:
    """Fetch OSM features within the bounding box of the isochrones and intersect them with the isochrones."""

    if pois_service is None:
        pois_service = PoisService()
    
    bbox = get_isochrones_bbox(isochrones)

    pois = await pois_service.get_pois(bbox=bbox, categories=categories)
    if pois is None or pois.get("features") is None or len(pois.get("features")) == 0:
        return None

    # Intersect isochrones with POIs
    pois_gdf = gpd.GeoDataFrame.from_features(pois)
    intersected_pois = intersect_isochrones(isochrones, pois_gdf)
    if intersected_pois is None or intersected_pois.empty:
        return None
    
    return intersected_pois