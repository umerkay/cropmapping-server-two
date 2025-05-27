import earthaccess
import rasterio
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from patchify import patchify
import pyproj
from rasterio.mask import mask
import re

# 1. Authenticate with NASA Earthdata
auth = earthaccess.login(strategy="netrc")

def search_hls_data(
        bounding_box,
        temporal_range,
        short_name='HLSS30',
        cloud_hosted=True,
        cloud_cover=(0, 20)
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

def extract_timestamp_from_filename(filename):
    """Extract the 3-digit timestamp from an HLS S30 filename."""
    match = re.search(r'\.(\d{4})(\d{3})T', os.path.basename(filename))
    if match:
        return match.group(2)  # Return the 3-digit timestamp
    return None

def extract_long_timestamp_from_filename(filename):
    """Extract the 'DDDTHHMMSS' portion from an HLS S30 filename."""
    match = re.search(r'\.(\d{3}T\d{6})', os.path.basename(filename))
    if match:
        return match.group(1)
    return None

def create_composite_image(img1_path, img2_path, output_path):
    """Create a composite image by filling NoData from img1 with img2."""
    with rasterio.open(img1_path) as src1:
        img1 = src1.read(masked=True)
        profile = src1.profile
        
    with rasterio.open(img2_path) as src2:
        img2 = src2.read(masked=True)
    
    # Create composite: use img1 where it has data, otherwise use img2
    composite = np.where(img1.mask, img2, img1)
    
    # Write the composite to file
    with rasterio.open(output_path, 'w', **profile) as dst:
        for i in range(composite.shape[0]):
            dst.write(composite[i], i+1)
    
    return output_path

def downloadTile(
    bounding_box=None,
    temporal_range=None,
    timestamps=None,
    output_dir='/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/tiles',
    short_name='HLSS30',
    cloud_hosted=True,
    cloud_cover=(0, 20),
    bands_required=['B02', 'B03', 'B04', 'B05', 'B06', 'B07'],
    filtered_results=None,
    valid_fraction_threshold=0.9,  # Keeping parameter for backwards compatibility
    tile_name=None
):
    if filtered_results:
        results = filtered_results
    else:
        if not bounding_box or not temporal_range:
            raise ValueError("Need bounding_box and temporal_range")
        results = search_hls_data(
            bounding_box=bounding_box,
            temporal_range=temporal_range,
            short_name=short_name,
            cloud_hosted=cloud_hosted,
            cloud_cover=cloud_cover
        )

    if not results:
        print("No results found.")
        return None, []
        
    download_dir = Path(output_dir)
    download_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = []
    
    # Handle different timestamp formats
    if timestamps is None:
        # Original behavior - select first, middle, last scenes
        if len(results) < 3:
            print("Not enough results to choose 3 scenes.")
            return None, []
            
        selected_scenes = [results[0], results[len(results)//2], results[-1]]
        
        # Download required bands
        urls_to_download = []
        for scene in selected_scenes:
            for url in scene.data_links():
                if any(band in url for band in bands_required):
                    urls_to_download.append(url)
                    
        if urls_to_download:
            downloaded_files = earthaccess.download(urls_to_download, local_path=str(download_dir))
            print(f"Downloaded {len(downloaded_files)} files")
    
    elif isinstance(timestamps, tuple):
        if all(isinstance(item, str) for item in timestamps):
            # Case: timestamps = ('007', '052', '098') - Specific timestamps
            if len(timestamps) == 1:
                # Single timestamp - make three copies
                timestamp = timestamps[0]
                print(f"Looking for single timestamp: {timestamp}")
                
                matching_scenes = []
                for scene in results:
                    for url in scene.data_links():
                        if len(timestamp) == 10:
                            if extract_long_timestamp_from_filename(url) == timestamp:
                                matching_scenes.append(scene)
                                break
                        if extract_timestamp_from_filename(url) == timestamp:
                            matching_scenes.append(scene)
                            break
                
                if not matching_scenes:
                    print(f"No scenes found matching timestamp {timestamp}")
                    return None, []
                    
                # Take the first matching scene
                scene = matching_scenes[0]
                urls_to_download = [url for url in scene.data_links() 
                                   if any(band in url for band in bands_required)]
                
                if urls_to_download:
                    downloaded_files = earthaccess.download(urls_to_download, local_path=str(download_dir))
                    print(f"Downloaded {len(downloaded_files)} files for timestamp {timestamp}")
                    
                    # Make three copies of each file by renaming them
                    new_files = []
                    for file_path in downloaded_files:
                        base_path = Path(file_path)
                        for i in range(1, 3):  # Make 2 more copies (3 total)
                            new_path = download_dir / f"{base_path.stem}_{i}{base_path.suffix}"
                            # Copy the file
                            with open(file_path, 'rb') as src_file, open(new_path, 'wb') as dst_file:
                                dst_file.write(src_file.read())
                            new_files.append(str(new_path))
                    downloaded_files.extend(new_files)
            else:
                # Multiple specific timestamps
                print(f"Looking for specific timestamps: {timestamps}")
                
                all_urls_to_download = []  # Collect all URLs first
                
                for timestamp in timestamps:
                    matching_scenes = []
                    for scene in results:
                        for url in scene.data_links():
                            if len(timestamp) == 10:
                                if extract_long_timestamp_from_filename(url) == timestamp:
                                    matching_scenes.append(scene)
                                    break
                            if extract_timestamp_from_filename(url) == timestamp:
                                matching_scenes.append(scene)
                                break
                    
                    if matching_scenes:
                        # Take the first matching scene
                        scene = matching_scenes[0]
                        urls_for_timestamp = [url for url in scene.data_links() 
                                          if any(band in url for band in bands_required)]
                        
                        if urls_for_timestamp:
                            all_urls_to_download.extend(urls_for_timestamp)
                            print(f"Found {len(urls_for_timestamp)} files to download for timestamp {timestamp}")
                    else:
                        print(f"No scenes found matching timestamp {timestamp}")
                
                # Download all files at once
                if all_urls_to_download:
                    downloaded_files = earthaccess.download(all_urls_to_download, local_path=str(download_dir))
                    print(f"Downloaded {len(downloaded_files)} files for all timestamps")
        
        elif all(isinstance(item, tuple) for item in timestamps):
            # Case: timestamps = ((004, 007), (054, 062), (099, 102)) - Composite ranges
            print("Processing timestamp ranges for composites")
            
            composite_dir = download_dir / "composites"
            composite_dir.mkdir(parents=True, exist_ok=True)
            
            for i, timestamp_range in enumerate(timestamps):
                composite_files = []
                
                # Get all files for this timestamp range
                range_files = {}
                for band in bands_required:
                    range_files[band] = []
                
                for timestamp in timestamp_range:
                    matching_scenes = []
                    for scene in results:
                        for url in scene.data_links():
                            if len(timestamp) == 10:
                                if extract_long_timestamp_from_filename(url) == timestamp:
                                    matching_scenes.append(scene)
                                    break
                            if extract_timestamp_from_filename(url) == timestamp:
                                matching_scenes.append(scene)
                                break
                    
                    if matching_scenes:
                        # Take the first matching scene
                        scene = matching_scenes[0]
                        for url in scene.data_links():
                            for band in bands_required:
                                if band in url:
                                    range_files[band].append(url)
                
                # Download all files for the timestamp range
                all_urls = [url for band_urls in range_files.values() for url in band_urls]
                if all_urls:
                    range_downloaded_files = earthaccess.download(all_urls, local_path=str(download_dir))
                    downloaded_files.extend(range_downloaded_files)
                    
                    # Create composites for each band
                    for band in bands_required:
                        band_files = [f for f in range_downloaded_files if band in f]
                        if len(band_files) >= 2:
                            composite_path = str(composite_dir / f"HLS.S30.{tile_name}.composite_{i}_{band}.tif")
                            try:
                                create_composite_image(band_files[0], band_files[1], composite_path)
                                composite_files.append(composite_path)
                            except Exception as e:
                                print(f"Error creating composite for {band}: {e}")
                
                output_dir = str(composite_dir)
                downloaded_files.extend(composite_files)
    
    elif isinstance(timestamps, str):
        # Single timestamp as a string - make three copies
        timestamp = timestamps
        print(f"Looking for single timestamp: {timestamp}")
        
        matching_scenes = []
        for scene in results:
            for url in scene.data_links():
                if len(timestamp) == 10:
                    if extract_long_timestamp_from_filename(url) == timestamp:
                        matching_scenes.append(scene)
                        break
                if extract_timestamp_from_filename(url) == timestamp:
                    matching_scenes.append(scene)
                    break
        
        if not matching_scenes:
            print(f"No scenes found matching timestamp {timestamp}")
            return None, []
            
        # Take the first matching scene
        scene = matching_scenes[0]
        urls_to_download = [url for url in scene.data_links() 
                           if any(band in url for band in bands_required)]
        
        if urls_to_download:
            downloaded_files = earthaccess.download(urls_to_download, local_path=str(download_dir))
            print(f"Downloaded {len(downloaded_files)} files for timestamp {timestamp}")
            
            # Make three copies of each file by renaming them
            new_files = []
            for file_path in downloaded_files:
                base_path = Path(file_path)
                for i in range(1, 3):  # Make 2 more copies (3 total)
                    new_path = download_dir / f"{base_path.stem}_{i}{base_path.suffix}"
                    # Copy the file
                    with open(file_path, 'rb') as src_file, open(new_path, 'wb') as dst_file:
                        dst_file.write(src_file.read())
                    new_files.append(str(new_path))
            downloaded_files.extend(new_files)
    
    return output_dir, downloaded_files

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
