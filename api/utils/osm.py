import os
import geopandas as gpd

DEFAULT_AREA = "geneva"


def get_transit_routes(area: str | None = None) -> gpd.GeoDataFrame:
    """Get transit routes from the GeoParquet file for the specified area."""
    area = area or DEFAULT_AREA

    routes_path = f"./data/{area}/routes.parquet"
    if not os.path.exists(routes_path):
        raise FileNotFoundError(f"Routes GeoParquet file not found for area '{area}' at path: {routes_path}")
    
    routes_gdf = gpd.read_parquet(routes_path)
    return routes_gdf


def get_transit_stops(area: str | None = None) -> gpd.GeoDataFrame:
    """Get transit stops from the GeoParquet file for the specified area."""
    area = area or DEFAULT_AREA

    stops_path = f"./data/{area}/stops.parquet"
    if not os.path.exists(stops_path):
        raise FileNotFoundError(f"Stops GeoParquet file not found for area '{area}' at path: {stops_path}")
    
    stops_gdf = gpd.read_parquet(stops_path)
    return stops_gdf


def get_osm_path(area: str | None = None) -> str:
    """Get the path to the OSM GeoParquet file for the specified area."""
    area = area or DEFAULT_AREA

    osm_path = f"./data/{area}/filtered.osm.pbf" # TODO : would be nice to not hardcode this name, but it is currently generated like this in the generate_data.sh script
    if not os.path.exists(osm_path):
        raise FileNotFoundError(f"OSM GeoParquet file not found for area '{area}' at path: {osm_path}")
    
    return osm_path