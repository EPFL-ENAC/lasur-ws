import argparse
import os
import pathlib

from extractosm.transit import extract_all_transit_stops, extract_all_transit_routes

def main():
    parser = argparse.ArgumentParser(description="Generate GeoParquet from PBF")
    parser.add_argument(
        "input_path",
        type=str,
        help="Path to the input .osm.pbf file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Optional: Path to save the geoparquet file",
        default=None
    )

    args = parser.parse_args()
    input_file = pathlib.Path(args.input_path)

    # Logic to determine output path
    if args.output_dir is not None:
        output_folder = pathlib.Path(args.output_dir)
    else:
        output_folder = input_file.parent / input_file.stem.replace(".osm", "")
        os.makedirs(output_folder, exist_ok=True)

    print(f"Input:  {input_file}")
    print(f"Output folder: {output_folder}")
    
    make_geoparquet(input_file, output_folder)




def make_geoparquet(input_file: pathlib.Path, output_folder: pathlib.Path):
    print(f"Generating GeoParquet from {input_file}...")

    print("Extracting transit stops...")
    stops_output = output_folder / "stops.parquet"
    extract_all_transit_stops(
        osm_pbf_path=input_file,
        include_route_ids=True,
        output_path=stops_output
    )

    print("Extracting transit routes...")
    routes_output = output_folder / "routes.parquet"
    extract_all_transit_routes(
        osm_pbf_path=input_file,
        route_types=["train", "bus", "tram", "light_rail", "subway", "trolleybus"],
        group_by="route_master",
        include_stop_ids=True,
        output_path=routes_output
    )


if __name__ == "__main__":
    main()