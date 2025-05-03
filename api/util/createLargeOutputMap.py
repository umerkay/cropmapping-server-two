import os
import random
import string
import json
import shutil
from shutil import move
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from api.util.downloadTileEarthAccess import downloadTile, getTileBoundsInWGS84, search_hls_data
from api.util.patchifyTileForPrithvi import patchifyTile
from api.util.createMasks import createMasks
from api.util.stitch256masks import stitch256masks

def generate_random_name(length=8):
    """Generate a random name of fixed length."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def get_tile_name(filename):
    # Split the filename by periods
    parts = filename.split('.')
    
    # The tile name is the 3rd element in the list (index 2)
    tile_name = parts[2]
    
    return tile_name

def clear_directory(directory_path):
    """Clear all files in the specified directory."""
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)

def filter_results_by_tile(results, tile_name):
    """Filter results that contain the specified tile name in data links."""
    filtered_results = []
    for result in results:
        for file_url in result.data_links():
            if tile_name in file_url:
                filtered_results.append(result)
                break  # Found a match, no need to check other links
    return filtered_results

def create_single_map(results, tile_name, output_dir):
    # Clear the tiles directory before processing
    tiles_dir = '/home/vision-16/CropTypeMap/Portal/server/tempData/tiles'
    clear_directory(tiles_dir)
    
    # Step 1: Download the tiles for this specific tile name
    tiles_dir, tiff_files = downloadTile(None, None, filtered_results=results)
    print(f"Tiles for {tile_name} downloaded to: {tiles_dir}")
    
    directory = '/home/vision-16/CropTypeMap/Portal/server/tempData/tiles'
    # List all files and directories
    tiff_files = os.listdir(directory)
    tiff_files = [(directory + "/" + t) for t in tiff_files]
    
    if not tiff_files:
        print(f"No files found for tile {tile_name}")
        return None, None
    
    # Extract the tile name from the first file
    extracted_tile_name = get_tile_name(tiff_files[0])
    print(f"Tile name: {extracted_tile_name}")

    # Step 2: Patchify the tiles
    patches_dir = patchifyTile(tiff_files)
    print("Patches made in: ", patches_dir)

    # Step 3: Generate masks
    masks_dir = createMasks()
    print("Masks saved in: ", masks_dir)

    # Step 4: Stitch the masks and generate the output PNG
    output_png = stitch256masks()
    print(f"Stitched mask output: {output_png}")

    # Move the stitched PNG to the output folder
    new_png_path = os.path.join(output_dir, f"stitched_tile_{tile_name}.png")
    move(output_png, new_png_path)
    print(f"Moved stitched tile to: {new_png_path}")

    # Step 5: Get the bounds for the tile
    miny, maxy, maxx, minx = getTileBoundsInWGS84(tiff_files[0])

    # Step 6: Create JSON metadata for this tile
    json_data = {
        "description": f"UNet outputs for tile {extracted_tile_name}",
        "model": "UNet trained on Prithvi Crop Classification",
        "source": "NASA HLS Sentinel-2 30m",
        "tiles": [
            [
                f"stitched_tile_{tile_name}.png",
                maxy,
                miny,
                maxx,
                minx
            ]
        ]
    }

    # Save the JSON file in the same output directory
    json_path = os.path.join(output_dir, f"data_{tile_name}.json")
    with open(json_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)
    print(f"Saved metadata to: {json_path}")

    return new_png_path, json_path

def create_large_output_map(bounding_box, temporal_range):
    """Create maps for multiple tiles in a single operation."""
    # Define the tiles to process
    tiles = ["T42SXB", "T42SXA"]  # Add more tiles as needed
    
    # Step 1: Search data once with the given parameters
    results = search_hls_data(bounding_box, temporal_range)
    
    if not results:
        print("No results found for the search criteria")
        return None
    
    # Generate a single random name for the output directory
    random_name = generate_random_name()
    output_dir = os.path.join("mapdata", random_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Store information about all processed tiles
    all_tiles_info = {
        "name": random_name,
        "temporal_range": temporal_range,
        "tiles": []
    }
    
    # Process each tile
    for tile_name in tiles:
        print(f"Processing tile: {tile_name}")
        
        # Filter results for this specific tile
        filtered_results = filter_results_by_tile(results, tile_name)
        
        if not filtered_results:
            print(f"No results found for tile {tile_name}")
            continue
        
        # Create the map for this tile
        png_path, json_path = create_single_map(filtered_results, tile_name, output_dir)
        
        if png_path and json_path:
            # Record the tile information
            all_tiles_info["tiles"].append({
                "tile_name": tile_name,
                "png_file": os.path.basename(png_path),
                "json_file": os.path.basename(json_path)
            })
    
    # Save the master JSON file with information about all tiles
    master_json_path = os.path.join(output_dir, "master.json")
    with open(master_json_path, 'w') as json_file:
        json.dump(all_tiles_info, json_file, indent=4)
    print(f"Saved master JSON to: {master_json_path}")
    
    return output_dir

if __name__ == "__main__":
    bounding_box = (69.31055, 27.96602, 75.28711, 34.08213)  # Replace with actual bounding box
    temporal_range = ("2024-01-01", "2024-5-15")  # Replace with actual date range
    output_dir = create_large_output_map(bounding_box, temporal_range)
    print(f"Output directory: {output_dir}")