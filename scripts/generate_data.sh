#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# --- Variables ---
ROOT_FOLDER="./data"
AREA_NAME="geneva"
GEOFABRIK_FOLDER="$ROOT_FOLDER/geofabrik/$AREA_NAME"
MERGED_PBF="$ROOT_FOLDER/geofabrik/$AREA_NAME-merged.osm.pbf"

EXTRACTED_PBF="$ROOT_FOLDER/$AREA_NAME-all.osm.pbf"
DESTINATION_FOLDER="$ROOT_FOLDER/$AREA_NAME"
FILTERED_PBF="$DESTINATION_FOLDER/filtered.osm.pbf"

URLS=(
  "https://download.geofabrik.de/europe/switzerland-latest.osm.pbf"
  "https://download.geofabrik.de/europe/france/rhone-alpes-latest.osm.pbf"
  "https://download.geofabrik.de/europe/france/franche-comte-latest.osm.pbf"
  "https://download.geofabrik.de/europe/france/alsace-latest.osm.pbf"
  "https://download.geofabrik.de/europe/france/bourgogne-latest.osm.pbf"
  "https://download.geofabrik.de/europe/italy/nord-ovest-latest.osm.pbf"
)

# --- Functions ---

pbf_download() {
    echo "Downloading latest OSM PBF file for Switzerland..."
    rm -rf "$GEOFABRIK_FOLDER"
    mkdir -p "$GEOFABRIK_FOLDER"

    printf "%s\n" "${URLS[@]}" | xargs -n 1 -P 4 wget -N -P "$GEOFABRIK_FOLDER"
}

pbf_merge() {
    echo "Merging PBF files..."
    rm -f "$MERGED_PBF"
    osmium merge -o "$MERGED_PBF" "$GEOFABRIK_FOLDER"/*.osm.pbf
}

pbf_extract() {
    echo "Extracting OSM data for $AREA_NAME area..."
    rm -f "$ROOT_FOLDER/$AREA_NAME-*.osm.pbf"
    
    # Ensure output directory exists
    mkdir -p "$ROOT_FOLDER"
    mkdir -p "$DESTINATION_FOLDER"
    
    # Extract bounding box
    osmium extract -b 4.7,45.1,10.5,47.8 "$MERGED_PBF" -o "$EXTRACTED_PBF"
    
    # Filter tags
    osmium tags-filter "$EXTRACTED_PBF" --overwrite -o "$FILTERED_PBF" \
        n/amenity,n/healthcare,n/office,n/shop,n/tourism,a/amenity,a/healthcare,a/office,a/shop,a/tourism \
		n/public_transport,n/highway=bus_stop,n/railway \
		a/public_transport \
		nwr/route=bus,tram,train,subway,trolleybus,light_rail,ferry,monorail \
		r/type=route_master \
		r/public_transport=stop_area
}

get_data() {
    time pbf_download
    time pbf_merge
    time pbf_extract
    
    echo "Generating GeoParquet..."
    
    mkdir -p "$DESTINATION_FOLDER"
    time poetry run python ./scripts/generate_geoparquet.py "$FILTERED_PBF" --output-dir "$DESTINATION_FOLDER"
}

cleanup() {
    echo "Cleaning up intermediate files..."
    rm -rf "$ROOT_FOLDER/geofabrik"
    rm -f "$EXTRACTED_PBF"
}

# --- Execution ---

get_data
cleanup