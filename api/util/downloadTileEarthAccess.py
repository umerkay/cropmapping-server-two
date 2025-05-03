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

def search_hls_data(
        bounding_box,
        temporal_range,
        short_name='HLSS30',
        cloud_hosted=True,
        cloud_cover=(0, 30)
        ):
    """Search for HLS data using the provided parameters."""
    
    print(f"Searching for data with bounding box: {bounding_box}")
    
    # Search for the dataset in cloud-hosted format
    results = earthaccess.search_data(
        short_name=short_name,
        cloud_hosted=cloud_hosted,
        temporal=temporal_range,
        bounding_box=(bounding_box[0], bounding_box[1], bounding_box[2], bounding_box[3]),
        cloud_cover=cloud_cover,
    )

    if len(results) < 3:
        print(f"Only {len(results)} results found, which is insufficient")
        return None
    
    print(f"Found {len(results)} results")
    return results

def downloadTile(
        bounding_box=None,
        temporal_range=None,
        output_dir='tempData/tiles',
        short_name='HLSS30',
        cloud_hosted=True,
        cloud_cover=(0, 30),
        bands_required = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07'],
        filtered_results=None
        ):
    
    # Use filtered results if provided, otherwise search for data
    if filtered_results:
        results = filtered_results
    else:
        if not bounding_box or not temporal_range:
            raise ValueError("Either filtered_results or both bounding_box and temporal_range must be provided")
        
        results = search_hls_data(
            bounding_box=bounding_box,
            temporal_range=temporal_range,
            short_name=short_name,
            cloud_hosted=cloud_hosted,
            cloud_cover=cloud_cover
        )
    
    if not results:
        print("No results available")
        return None, []
    
    # Select a subset of results (beginning, middle, end)
    if len(results) >= 3:
        selected_results = [results[0], results[len(results)//2], results[-1]]
    else:
        selected_results = results

    download_dir = Path(output_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    rgb_files = []

    # Loop over results and check the available files
    for result in selected_results:
        # Check the file URLs in the result
        for file_url in result.data_links():
            for band in bands_required:
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
