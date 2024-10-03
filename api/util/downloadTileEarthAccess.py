import earthaccess
import rasterio
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from patchify import patchify
import pyproj

# 1. Authenticate with NASA Earthdata
auth = earthaccess.login(strategy="netrc")

# bounding_box = (72.49658, 32.98648, 72.66797, 33.14018)
# temporal_range = ("2023-04-01", "2023-12-01")

def downloadTile(
        bounding_box,
        temporal_range,
        output_dir='tempData/tiles',
        short_name='HLSS30',
        cloud_hosted=True,
        cloud_cover=(0, 30),
        rgb_bands = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07']
        ):
    
    print(bounding_box)
    
    # 3. Search for the dataset (e.g., Sentinel-2 or Landsat-8) in cloud-hosted format
    results = earthaccess.search_data(
        short_name=short_name,
        cloud_hosted=cloud_hosted,  # Prefer cloud-hosted data for easy access
        temporal=temporal_range,  # Specify the date range of interest
        bounding_box=(bounding_box[0], bounding_box[1], bounding_box[2], bounding_box[3]),  # Use the bounding box filter,
        cloud_cover=cloud_cover,  # Filter for images with less than 30% cloud cover
    )

    if (len(results) < 3):
        print("No results found")
        return None
    
    selected_results = results[0], results[len(results)//2], results[-1]
      # Blue, Green, Red, NIR, SWIR, SWIR 2

    download_dir = Path(output_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    rgb_files = []

    # Loop over results and check the available files
    for result in selected_results:
        # Check the file URLs in the result
        for file_url in result.data_links():
            for band in rgb_bands:
                if band in file_url:  # Check if the file URL contains the RGB band name
                    band_file = earthaccess.download(file_url, local_path=str(download_dir))
                    if band_file:
                        rgb_files.append(band_file)
                        break  # Move to the next band once the current one is found

    return output_dir, rgb_files


def getTileBoundsInWGS84(tile):
    with rasterio.open(tile) as src:
        bounds = src.bounds
        crs = src.crs

    # Get the EPSG code of the CRS
    epsg_code = crs.to_epsg()
    # Create a PyProj CRS object
    crs_proj = pyproj.CRS.from_epsg(epsg_code)
    # Get the WGS84 CRS
    wgs84 = pyproj.CRS("EPSG:4326")
    # Create a transformer
    transformer = pyproj.Transformer.from_crs(crs_proj, wgs84, always_xy=True)
    # Transform the bounds to WGS84
    minx, miny = transformer.transform(bounds.left, bounds.bottom)
    maxx, maxy = transformer.transform(bounds.right, bounds.top)

    #return north, south, east, west
    return miny, maxy, maxx, minx
