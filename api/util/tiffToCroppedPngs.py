#!/usr/bin/env python3
"""
Process UNet‐classified TIFF tiles into per‐district PNGs and JSON summaries.

Usage:
    python process_tiles.py \
        --tile-json-dir /path/to/tile_jsons \
        --district-geojson /path/to/districts.json \
        --output-png-dir croppedPngs \
        --output-json-dir jsonData \
        --season January \
        --year 2025
"""

import os
import json
import argparse

import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.transform import from_bounds
from rasterio.io import MemoryFile
from rasterio.mask import mask
import geopandas as gpd

def main(tile_json_dir, district_geojson, output_png_dir, output_json_dir, season, year):
    # 1. Read tile metadata JSONs
    tile_meta_list = []
    for fname in os.listdir(tile_json_dir):
        if not fname.lower().endswith('.json'):
            continue
        if fname in ('master.json', 'data.json'):
            continue
        path = os.path.join(tile_json_dir, fname)
        with open(path) as f:
            tile_meta_list.append(json.load(f))

    if not tile_meta_list:
        raise RuntimeError("No valid tile JSON files found in " + tile_json_dir)

    # 2. Build in‐memory mosaic
    src_datasets = []
    for meta in tile_meta_list:
        tiff_path = os.path.join(tile_json_dir, meta["classification_tiff"])
        # extract [png_name, lat_max, lat_min, lon_max, lon_min]
        _, lat_max, lat_min, lon_max, lon_min = meta["tiles"][0]
        with rasterio.open(tiff_path) as src:
            data = src.read(1)
            profile = src.profile.copy()

        # override transform & CRS
        transform = from_bounds(
            lon_min, lat_min, lon_max, lat_max,
            width=profile["width"], height=profile["height"]
        )
        profile.update({
            "driver": "GTiff",
            "count": 1,
            "transform": transform,
            "crs": "EPSG:4326"
        })
        memfile = MemoryFile()
        ds = memfile.open(**profile)
        ds.write(data, 1)
        src_datasets.append(ds)

    mosaic_arr, mosaic_transform = merge(src_datasets, nodata=-1)
    # create in‐memory mosaic dataset
    mono_dtype = mosaic_arr.dtype
    out_profile = {
        "driver": "GTiff",
        "height": mosaic_arr.shape[1],
        "width": mosaic_arr.shape[2],
        "count": 1,
        "dtype": mono_dtype,
        "crs": "EPSG:4326",
        "transform": mosaic_transform
    }
    mem_mosaic = MemoryFile()
    mosaic_ds = mem_mosaic.open(**out_profile)
    mosaic_ds.write(mosaic_arr[0], 1)

    # 3. Load and filter districts to Punjab
    districts = gpd.read_file(district_geojson, force_pyogrio=False)  # fall back to Fiona
    # Repair invalid geometries with zero-width buffer
    districts["geometry"] = districts.geometry.buffer(0)
    # Drop any remaining invalid geometries
    districts = districts[districts.is_valid]
    
    punjab = districts[districts["NAME_1"] == "Punjab"]
    if punjab.empty:
        raise RuntimeError("No districts found with NAME_1 == 'Punjab'")

    # 4. Define color & group mappings
    color_map = {
        0: (194, 81, 0),
        13: (194, 81, 0),
        6: (194, 81, 0),
        7:(0,100,0),
        1: (0,100,0),
        2: (0,100,0),

        3: (255, 166, 0),
        4: (255, 166, 0),
        8: (255, 166, 0),
        9: (255, 166, 0),
        12:(255, 166, 0),

        10:(212, 255, 71),
        5: (212, 255, 71),
        11:(212, 255, 71)
    }
    crop_groups = {
        "Wheat": [3,4,8,9,12],
        "Cotton": [],
        "Others": [10,5,11]
    }
    landuse_groups = {
        "Natural": [1,2,7],
        "Urban/Barren": [6, 13, 0],
    }

    # per‐pixel area (30m × 30m → acres)
    pixel_area_acres = (30 * 30) / 4046.85642 / 2

    # 5. Prepare output directories
    os.makedirs(output_png_dir, exist_ok=True)
    os.makedirs(output_json_dir, exist_ok=True)

    # accumulators for province‐wide totals
    total_crop = {k: 0 for k in crop_groups}
    total_land = {k: 0 for k in landuse_groups}

    # 6. Loop through each district
    for _, row in punjab.iterrows():
        district_name = row["NAME_3"].replace(" ", "_")
        shapes = [row.geometry]

        # a) Clip mosaic to district
        out_img, out_transform = mask(
            dataset=mosaic_ds,
            shapes=shapes,
            crop=True,
            filled=True,
            nodata=-1  # Changed from 0 to -1
        )
        arr = out_img[0]
        h, w = arr.shape

        # b) Colorize
        rgba = np.zeros((h, w, 4), dtype=np.uint8)

        # Make everything transparent initially
        rgba[:, :, 3] = 0

        # Set alpha to opaque only for valid (non-nodata) pixels
        rgba[arr != -1, 3] = 255

        # Apply color mapping only to valid pixels
        for cls, col in color_map.items():
            mask_cls = (arr == cls)
            rgba[mask_cls, 0:3] = col
        
        # No need to handle no data values inside district - leave them transparent

        # c) Save PNG
        png_fname = f"{season}_{year}_{district_name}.png"
        png_path = os.path.join(output_png_dir, png_fname)
        png_profile = {
            "driver": "PNG",
            "height": h,
            "width": w,
            "count": 4,  # Changed from 3 to 4 for RGBA
            "dtype": rgba.dtype,
            "transform": out_transform,
            "crs": "EPSG:4326"
        }
        with rasterio.open(png_path, 'w', **png_profile) as dst:
            dst.write(rgba.transpose(2,0,1))

        # d) Compute pixel counts
        unique, counts = np.unique(arr, return_counts=True)
        cls_counts = dict(zip(unique.tolist(), counts.tolist()))

        # e) Summarize into areas
        crop_data = {}
        for label, classes in crop_groups.items():
            px = sum(cls_counts.get(c, 0) for c in classes)
            acres = round(px * pixel_area_acres)
            crop_data[label] = acres
            total_crop[label] += acres

        land_data = {}
        for label, classes in landuse_groups.items():
            px = sum(cls_counts.get(c, 0) for c in classes)
            acres = round(px * pixel_area_acres)
            land_data[label] = acres
            total_land[label] += acres

        # f) Write district JSON
        info = {
            "description": f"Land and Crop data for {row['NAME_3']} for {season} {year}",
            "cropTypeData": crop_data,
            "landUseData": land_data
        }
        json_fname = f"{season}_{year}_{district_name}.json"
        with open(os.path.join(output_json_dir, json_fname), 'w') as jf:
            json.dump(info, jf, indent=2)

        break

    # 7. Save province‐wide summary
    prov_info = {
        "description": f"Land and Crop data for Punjab for {season} {year}",
        "cropTypeData": total_crop,
        "landUseData": total_land
    }
    prov_fname = f"{season}_{year}_Punjab.json"
    with open(os.path.join(output_json_dir, prov_fname), 'w') as pf:
        json.dump(prov_info, pf, indent=2)

    print("Processing complete.")
    print(f"  - PNGs in:  {output_png_dir}")
    print(f"  - JSONs in: {output_json_dir}")

if __name__ == "__main__":
    # Set variables directly instead of using command line arguments
    tile_json_dir = "/home/umer/projects/vector_studio/icons/cropmapping-server-two/mapdata/Jan-Apr_2025_Punjab"  # Directory containing your tile JSON files and TIFFs
    district_geojson = "/home/umer/projects/vector_studio/icons/cropmapping-server-two/districts_cleaned.json"  # Path to the district GeoJSON file
    output_png_dir = "/home/umer/projects/vector_studio/icons/cropmapping-server-two/mapdata/Jan-Apr_2025_Punjab/croppedPngsTest"  # Directory to save Punjab PNG
    output_json_dir = "/home/umer/projects/vector_studio/icons/cropmapping-server-two/mapdata/Jan-Apr_2025_Punjab/jsonDataTest"  # Directory to save Punjab JSON summary
    season = "Jan-Apr"  # Season or month name
    year = 2025  # Year
    
    main(tile_json_dir, district_geojson, output_png_dir, output_json_dir, season, year)
