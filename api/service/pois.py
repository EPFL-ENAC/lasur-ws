import logging
from typing import Dict
import pandas as pd
from geopandas import GeoDataFrame
from isochrones import get_osm_features
from ..cache import redis
from ..models.isochrones import FeatureCollection
from ..config import config
import hashlib
import json


class PoisService:
    def __init__(self):
        self.areas = json.loads(config.CACHE_OSM_AREAS)
        self.categories = [category.strip()
                           for category in config.CACHE_OSM_CATEGORIES.split(",")]

    async def get_pois(self, bbox: list[float], categories: list[str] = None, cached: bool = True) -> FeatureCollection:
        """Get available OSM features for isochrone calculations.
        If no bbox or categories are provided, use default from config.

        Args:
            bbox (list[float]): Bounding box [min_lon, min_lat, max_lon, max_lat].
            categories (list[str], optional): List of OSM categories. Defaults to None.
            cached (bool, optional): Whether to use cached data. Defaults to True.

        Returns:
            FeatureCollection: GeoJSON FeatureCollection of OSM features.
        """
        try:
            if cached:
                area = self._get_area(bbox)
                if area:
                    # get cached data for each category and concatenate them
                    all_features = GeoDataFrame()
                    for category in categories if categories else self.categories:
                        features = await self._make_area_category_cache(area, category)
                        if features is not None and not features.empty:
                            all_features = pd.concat(
                                [all_features, features], ignore_index=True)
                    return all_features.__geo_interface__
                else:
                    logging.warning(
                        "Bounding box is outside of cached areas. Fetching live data.")
            else:
                logging.info("Bypassing cache. Fetching live data.")

            # Fetch live data from OSM
            features = get_osm_features(
                bbox, tags=self._make_tags(categories if categories else self.categories), crs="EPSG:4326")
            return features.__geo_interface__
        except Exception as e:
            logging.error(e, exc_info=True)
            return FeatureCollection(type="FeatureCollection", features=[], bbox=bbox)

    async def delete_cache(self) -> None:
        """Delete all cached OSM features."""
        try:
            keys = await redis.keys("pois:*")
            if keys:
                await redis.delete(*keys)
                logging.info(f"Deleted {len(keys)} cache keys.")
            else:
                logging.info("No cache keys to delete.")
        except Exception as e:
            logging.error(e, exc_info=True)

    async def make_cache(self) -> Dict:
        """Get available OSM features for isochrone calculations and cache them."""
        counts = {}
        for area in self.areas:
            features = await self._make_area_cache(area)
            if features is None:
                continue
            # count rows in this pandas dataframe grouped by 'variable' column
            area_counts = features['variable'].value_counts(
            ).to_dict()
            for category, count in area_counts.items():
                counts[category] = counts.get(category, 0) + count
        return counts

    async def _make_area_cache(self, bbox: list[float]) -> GeoDataFrame | None:
        """Get available OSM features for isochrone calculations and cache them."""
        try:
            all_features = GeoDataFrame()
            for category in self.categories:
                features = await self._make_area_category_cache(bbox, category)
                if features is None or features.empty:
                    continue  # No data fetched for this category
                all_features = pd.concat(
                    [all_features, features], ignore_index=True)
            return all_features
        except Exception as e:
            logging.error(e, exc_info=True)
            return None

    async def delete_cache(self) -> None:
        """Delete all cached OSM features."""
        try:
            keys = await redis.keys("pois:*")
            if keys:
                await redis.delete(*keys)
                logging.info(f"Deleted {len(keys)} cache keys.")
            else:
                logging.info("No cache keys to delete.")
        except Exception as e:
            logging.error(e, exc_info=True)

    async def make_cache(self) -> Dict:
        """Get available OSM features for isochrone calculations and cache them."""
        counts = {}
        for area in self.areas:
            features = await self._make_area_cache(area)
            # count rows in this pandas dataframe grouped by 'variable' column
            area_counts = features['variable'].value_counts(
            ).to_dict()
            for category, count in area_counts.items():
                counts[category] = counts.get(category, 0) + count
        return counts

    async def _make_area_cache(self, bbox: list[float]) -> GeoDataFrame | None:
        """Get available OSM features for isochrone calculations and cache them."""
        try:
            all_features = GeoDataFrame()
            for category in self.categories:
                features = await self._make_area_category_cache(bbox, category)
                if features is None or features.empty:
                    continue  # No data fetched for this category
                all_features = pd.concat(
                    [all_features, features], ignore_index=True)
            return all_features
        except Exception as e:
            logging.error(e, exc_info=True)
            return None

    async def _make_area_category_cache(self, bbox: list[float], category: str) -> GeoDataFrame | None:
        """Get available OSM features for a specific category and cache them."""
        try:
            cache_key = self._make_cache_key(bbox, category)
            # Check if the data is already cached
            cached_data_json_str = await redis.get(cache_key)
            if cached_data_json_str:
                logging.info(f"Cache hit for key: {cache_key}")
                # json string to dict
                cached_data = json.loads(cached_data_json_str)
                return GeoDataFrame.from_features(cached_data)
            logging.info(f"Cache miss for key: {cache_key}. Fetching data...")
            features = get_osm_features(
                bbox, tags=self._make_tags([category]), crs="EPSG:4326")
            if features is None or features.empty:
                return None  # No data fetched for this category
            # Store the fetched data in the cache with an expiry time
            await redis.set(cache_key,
                            features.to_json(), ex=config.CACHE_OSM_EXPIRY)
            return features
        except Exception as e:
            logging.error(e, exc_info=True)
            return None

    def _make_tags(self, categories: list[str]) -> Dict[str, bool]:
        tags = {}
        for category in categories:
            tags[category] = True
        return tags

    def _make_cache_key(self, bbox: list[float], category: str) -> str:
        """Create a cache key for the given category and the current bounding box.

        Args:
            category (str): The category to include in the cache key.

        Returns:
            str: The generated cache key.
        """
        bbox_str = ",".join(map(str, bbox))
        cache_string = f"{category}:{bbox_str}"
        return f"pois:{hashlib.md5(cache_string.encode()).hexdigest()}"

    def _get_area(self, bbox: list[float]) -> list[float] | None:
        """Get the area that includes the bounding box.

        Args:
            bbox (list[float]): Bounding box [min_lon, min_lat, max_lon, max_lat].

        Returns:
            list[float] | None: The area if found, else None.
        """
        for area in self.areas:
            if bbox[0] >= area[0] and bbox[1] >= area[1] and bbox[2] <= area[2] and bbox[3] <= area[3]:
                return area
        return None
