#!/usr/bin/env python3
"""
remove_invalid_districts.py

Read a GeoJSON FeatureCollection, drop any Feature whose Polygon
exterior ring has exactly two points, and write out a cleaned GeoJSON.

Usage:
    python remove_invalid_districts.py \
        --input /path/to/districts.json \
        --output /path/to/districts_cleaned.json
"""

import json
import argparse
import sys

def is_invalid_geom(geom):
    """
    Returns True if this geometry has an exterior ring with exactly two points.
    Handles Polygon and MultiPolygon.
    """
    gtype = geom.get("type")
    coords = geom.get("coordinates", [])

    if gtype == "Polygon":
        # coords = [ exterior_ring, [hole1], ... ]
        exterior = coords[0] if coords else []
        return len(exterior) == 2

    elif gtype == "MultiPolygon":
        # coords = [ [ exterior, hole... ], [ ... ], ... ]
        for poly in coords:
            if poly and len(poly[0]) == 2:
                return True
        return False

    # for other geometry types, we keep them
    return False

def main():
    p = argparse.ArgumentParser(
        description="Remove features whose Polygon exterior ring has 2 points."
    )
    p.add_argument("--input",  "-i", required=True,
                   help="Path to input GeoJSON (FeatureCollection).")
    p.add_argument("--output", "-o", required=True,
                   help="Path to write cleaned GeoJSON.")
    args = p.parse_args()

    # Load raw JSON so we can skip shapely/geopandas parsing
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    if data.get("type") != "FeatureCollection" or "features" not in data:
        print("ERROR: not a valid FeatureCollection", file=sys.stderr)
        sys.exit(1)

    features = data["features"]
    cleaned = []
    removed_count = 0

    for feat in features:
        geom = feat.get("geometry")
        if geom and is_invalid_geom(geom):
            removed_count += 1
            continue
        cleaned.append(feat)

    print(f"Removed {removed_count} invalid feature(s) out of {len(features)} total.")

    # Write cleaned GeoJSON
    data["features"] = cleaned
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error writing {args.output}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Cleaned GeoJSON written to {args.output}")

if __name__ == "__main__":
    main()
