import numpy as np
import geopandas as gpd


def sanitize_df(df):
    """Convert all numpy arrays in 'object' columns to python lists."""
    df = df.copy()
    for col in df.columns:
        # If the column contains objects (like lists/arrays)
        if df[col].dtype == 'object':
            df[col] = df[col].apply(
                lambda x: x.tolist() if isinstance(x, np.ndarray) else x
            )
    return df


def gdf_geo_interface_or_none(df: gpd.GeoDataFrame | None):
    """Return the __geo_interface__ of the GeoDataFrame or None if the input is None."""
    if df is None:
        return None
    
    return df.__geo_interface__