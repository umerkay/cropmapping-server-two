import os
import random
import string
import json
from shutil import move
from api.util.downloadTileEarthAccess import downloadTile, getTileBoundsInWGS84
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

def create_map(bounding_box, temporal_range):
    # Step 1: Download the tiles
    tiles_dir, tiff_files = downloadTile(bounding_box, temporal_range)
    print("Tiles downloaded to: ", tiles_dir)
    directory = '/home/vision-16/CropTypeMap/Portal/server/tempData/tiles'
    # print("hi")
    # List all files and directories
    tiff_files = os.listdir(directory)
    tiff_files = [(directory + "/" + t) for t in tiff_files]
    # Extract the tile name from the first file (assuming it's in the filename)
    tile_name = get_tile_name(tiff_files[0]) #os.path.basename(tiff_files[0]).split('.')[0]
    print(f"Tile name: {tile_name}")

    # Step 2: Patchify the tiles
    patches_dir = patchifyTile(tiff_files)
    print("Patches made in: ", patches_dir)

    # Step 3: Generate masks
    masks_dir = createMasks()
    print("Masks saved in: ", masks_dir)

    # Step 4: Stitch the masks and generate the output PNG
    output_png = stitch256masks()
    print(f"Stitched mask output: {output_png}")

    # Step 5: Generate a random name
    random_name = generate_random_name()

    # Create a new directory to save the output PNG and JSON
    output_dir = os.path.join("mapdata", random_name)
    os.makedirs(output_dir, exist_ok=True)

    # Move the stitched PNG to the new folder
    new_png_path = os.path.join(output_dir, "stitched_tile.png")
    move(output_png, new_png_path)
    print(f"Moved stitched tile to: {new_png_path}")

    # Step 6: Get the bounds for the tile
    miny, maxy, maxx, minx = getTileBoundsInWGS84(tiff_files[0])

    # Step 7: Create JSON metadata
    json_data = {
        "name": random_name,
        "description": f"(Test only) UNet outputs for tile {tile_name}",
        "model": "UNet trained on Prithvi Crop Classification",
        "source": "NASA HLS Sentinel-2 30m",
        "tiles": [
            [
                "stitched_tile.png",
                maxy,
                miny,
                maxx,
                minx
            ]
        ]
    }

    # Step 8: Save the JSON file in the same output directory
    json_path = os.path.join(output_dir, "data.json")
    with open(json_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)
    print(f"Saved metadata to: {json_path}")

    return new_png_path, json_path
