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

OSM_TAGS = {
    "amenity": [
        "restaurant",
        "cafe",
        "school",
        "fast_food",
        "post_box",
        "pharmacy",
        "bar",
        "bank",
        "car_sharing",
        "community_centre",
        "theatre",
        "social_facility",
        "doctors",
        "library",
        "university",
        "pub",
        "post_office",
        "college",
        "car_rental",
        "bbq",
        "police",
        "nightclub",
        "hospital",
        "townhall",
        "dentist",
        "charging_station",
        "public_bookcase",
        "waste_disposal",
        "public_building",
        "ferry_terminal",
        "clinic",
        "cinema",
        "music_school",
        "bicycle_rental",
        "bicycle_repair_station",
        "veterinary",
        "arts_centre",
        "toy_library",
        "childcare",
        "public_bath",
        "events_venue",
        "marketplace",
        "social_centre",
        "exhibition_centre",
        "bus_station",
        "concert_hall",
        "biergarten",
        "food_court",
        "library_dropoff",
        "prep_school"
    ],
    "healthcare": [
        "pharmacy",
        "doctor",
        "alternative",
        "physiotherapist",
        "hospital",
        "dentist",
        "clinic",
        "laboratory",
        "podiatrist",
        "psychotherapist",
        "centre",
        "audiologist",
        "birthing_centre",
        "blood_donation",
        "optometrist",
        "psychomotricist"
    ],
    "office": [
        "coworking", "administrative"
    ],
    "public_transport": [
        "stop_position",
        "platform",
        "station"
    ],
    "shop": [
        "clothes",
        "supermarket",
        "convenience",
        "bakery",
        "kiosk",
        "bicycle_rental",
        "department_store",
        "shoes",
        "books",
        "florist",
        "dry_cleaning",
        "optician",
        "laundry",
        "sports",
        "butcher",
        "mall",
        "pastry",
        "coffee",
        "second_hand",
        "tea",
        "art",
        "copyshop",
        "medical_supply",
        "grocery",

    ],
    "tourism": [
        "artwork",
        "hotel",
        "information",
        "attraction",
        "museum",
        "viewpoint",
        "gallery",
        "zoo",
        "picnic_site",
        "theme_park",
        "camp_site",
        "chalet",
        "motel"
    ],
}

CATEGORY_TAGS = {
    "food": {
        "amenity": [
            "restaurant",
            "cafe",
            "fast_food",
            "food_court"
        ],
        "shop": [
            "supermarket",
            "convenience",
            "bakery",
            "butcher",
            "pastry"
        ]
    },
    "education": {
        "amenity": [
            "school",
            "library",
            "university",
            "college",
            "public_bookcase",
            "waste_disposal",
            "toy_library",
            "childcare",
            "library_dropoff",
            "prep_school",
        ]
    },
    "service": {
        "amenity": [
            "post_box",
            "bank",
            "post_office",
            "police",
            "townhall",
            "public_building",
            "public_bath",
        ],
        "office": [
            "coworking",
            "administrative"
        ],
        "shop": [
            "dry_cleaning",
            "laundry",
            "copyshop"
        ]
    },
    "health": {
        "amenity": [
            "pharmacy",
            "doctors",
            "hospital",
            "dentist",
            "clinic",
            "veterinary",
        ],
        "healthcare": [
            "pharmacy",
            "doctor",
            "alternative",
            "physiotherapist",
            "hospital",
            "dentist",
            "clinic",
            "laboratory",
            "podiatrist",
            "psychotherapist",
            "centre",
            "audiologist",
            "birthing_centre",
            "blood_donation",
            "optometrist",
            "psychomotricist"
        ]
    },
    "leisure": {
        "amenity": [
            "bar",
            "community_centre",
            "theatre",
            "social_facility",
            "pub",
            "bbq",
            "nightclub",
            "cinema",
            "music_school",
            "arts_centre",
            "events_venue",
            "social_centre",
            "exhibition_centre",
            "concert_hall",
            "biergarten"
        ],
        "shop": ["art"],
        "tourism": [
            "artwork",
            "hotel",
            "information",
            "attraction",
            "museum",
            "viewpoint",
            "gallery",
            "zoo",
            "picnic_site",
            "theme_park",
            "camp_site",
            "chalet",
            "motel"
        ]
    },
    "transport": {
        "amenity": [
            "car_sharing",
            "car_rental",
            "charging_station",
            "ferry_terminal",
            "bicycle_rental",
            "bicycle_repair_station",
            "bus_station",
        ],
        "public_transport": [
            "stop_position",
            "platform",
            "station"
        ]
    },
    "commerce": {
        "amenity": ["marketplace"],
        "shop": [
            "clothes",
            "kiosk",
            "bicycle",
            "department_store",
            "shoes",
            "books",
            "florist",
            "sports",
            "mall",
            "coffee",
            "second_hand",
            "tea",
            "grocery"
        ]
    },
}


class PoisService:
    def __init__(self):
        self.areas = json.loads(config.CACHE_OSM_AREAS)
        self.categories = CATEGORY_TAGS.keys()

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
                            inner_features = features.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
                            if inner_features is not None and not inner_features.empty:
                                all_features = pd.concat(
                                    [all_features, inner_features], ignore_index=True)
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
            if category in CATEGORY_TAGS:
                for tag, values in CATEGORY_TAGS[category].items():
                    if tag not in tags:
                        tags[tag] = []
                    for value in values:
                        if value not in tags[tag]:
                            tags[tag].append(value)
            elif category in OSM_TAGS:
                if category not in tags:
                    tags[category] = []
                for value in OSM_TAGS[category]:
                    if value not in tags[category]:
                        tags[category].append(value)
        logging.debug(f"Using OSM tags: {tags}")
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
