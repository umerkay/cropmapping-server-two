import os
import random
import string
import json
import shutil
from shutil import move
import sys
import traceback
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

def create_single_map(results, tile_name, timestamps, output_dir):
    # Clear the tiles directory before processing
    tiles_dir = '/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/tiles'
    clear_directory(tiles_dir)
    
    print(tile_name, timestamps)
    # return None, None, None
    # Step 1: Download the tiles for this specific tile name
    tiles_dir, tiff_files = downloadTile(None, None, tile_name=tile_name, filtered_results=results, timestamps=timestamps)
    if not tiles_dir or not tiff_files:
        print(f"Failed to download tiles for {tile_name}")
        return None, None, None
    print(f"Tiles for {tile_name} downloaded to: {tiles_dir}")
    
    # directory = '/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/tiles'
    # List all files and directories
    directory = tiles_dir
    tiff_files = os.listdir(directory)
    tiff_files = [(directory + "/" + t) for t in tiff_files]
    
    if not tiff_files:
        print(f"No files found for tile {tile_name}")
        return None, None, None
    
    # Extract the tile name from the first file
    extracted_tile_name = get_tile_name(tiff_files[0])
    print(f"Tile name: {extracted_tile_name}")

    # Step 2: Patchify the tiles - use memory approach
    patches, profile = patchifyTile(tiff_files, save_to_disk=False)
    print("Patches generated in memory with shape:", patches.shape)
    
    # For compatibility, still create the directory
    patches_dir = "tempData/patches"
    os.makedirs(patches_dir, exist_ok=True)

    # Step 3: Generate masks directly from patches in memory and get them back
    masks_dir, rgb_masks, class_masks = createMasks(input_patches=patches, profile=profile, return_memory_masks=True)
    print("Masks processed with", len(rgb_masks), "RGB masks and", len(class_masks), "class masks")

    # Step 4: Stitch the masks directly from memory
    output_png = stitch256masks(rgb_masks=rgb_masks, class_masks=class_masks)
    print(f"Stitched mask output: {output_png}")
    
    # Get the stitched TIFF path
    output_tiff = output_png.replace('.png', '.tiff')
    if os.path.exists(output_tiff):
        print(f"Stitched TIFF output: {output_tiff}")
    else:
        print(f"Warning: Expected TIFF file not found at {output_tiff}")
        output_tiff = None

    # Move the stitched PNG to the output folder
    new_png_path = os.path.join(output_dir, f"stitched_tile_{tile_name}.png")
    move(output_png, new_png_path)
    print(f"Moved stitched tile to: {new_png_path}")
    
    # Move the stitched TIFF if it exists
    new_tiff_path = None
    if output_tiff and os.path.exists(output_tiff):
        new_tiff_path = os.path.join(output_dir, f"stitched_tile_{tile_name}.tiff")
        move(output_tiff, new_tiff_path)
        print(f"Moved stitched class TIFF to: {new_tiff_path}")

    # Step 5: Get the bounds for the tile
    miny, maxy, maxx, minx = getTileBoundsInWGS84(tiff_files[0])

    # Step 6: Create JSON metadata for this tile
    json_data = {
        "description": f"Crop classification for tile {extracted_tile_name}",
        "model": "Prithvi 300M",
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
    
    # Add classification TIFF info if available
    if new_tiff_path:
        json_data["classification_tiff"] = os.path.basename(new_tiff_path)

    # Save the JSON file in the same output directory
    json_path = os.path.join(output_dir, f"data_{tile_name}.json")
    with open(json_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)
    print(f"Saved metadata to: {json_path}")

    return new_png_path, new_tiff_path, json_path

def create_large_output_map(bounding_box, temporal_range):
    """Create maps for multiple tiles in a single operation."""
    # Define the tiles to process
    # tiles = ['42RWA', '42RWT', '42RWU', '42RWV', '42RXA', '42RXT', '42RXU', '42RXV', '42RYA', '42RYR', '42RYS', '42RYT', '42RYU', '42RYV', '42SWA', '42SWB', '42SWC', '42SXA', '42SXB', '42SXC', '42SYA', '42SYB', '42SYC', '43RBL', '43RBM', '43RBN', '43RBP', '43RBQ', '43RBR', '43RCL', '43RCM', '43RCN', '43RCP', '43RCQ', '43RCR', '43RDL', '43RDM', '43RDN', '43RDP', '43RDQ', '43RDR', '43REL', '43REM', '43REN', '43REP', '43REQ', '43RER', '43SBR', '43SBS', '43SBT', '43SCR', '43SCS', '43SCT', '43SDR', '43SDS', '43SDT', '43SER', '43SES', '43SET']
    #punjab cleaned tiles, less
    # tiles = ['42RWU', '42RXT', '42RXU', '42RXV', '42RYR', '42RYS', '42RYT', '42RYU', '42RYV', '42SXA', '42SXB', '42SYA', '42SYB', '42SYC', '43RBM', '43RBN', '43RBP', '43RBQ', '43RCN', '43RCP', '43RCQ', '43RDP', '43RDQ', '43SBR', '43SBS', 
    # tiles = ['43SBT', '43SCR', '43SCS',
    # tiles = ['43SCT', '43SDR', '43SDS', '43SDT', '43SER', '42RWS', '42RXS']
    # timestamps = [ (('009', '016'), ('041', '048'), ('096', '097')), ('025', '065', '105'), ('025', '065', '097'), ('009' ,'041', '105'), '098', ('010', '074', '098'), ('026', '066', '098'), (('065', '074'), ('082', '089'), ('098', '105')), (('026', '033'), ('065','066'), ('098','105')), (('008','009'), ('064','065'), ('104','105')), (('008','009'), ('032','033'), ('104','105')), (('009','010'), ('041','042'), ('089','090')), (('009','010'), ('074','081'), ('089','090')), ('009', '065', '105'), (('003','010'), ('051','066'), ('091','098')), (('026','027'),('066','067'),('090','091')), (('026','027'),('066','067'),('090','091')), ('026','066','098'), ('027','075','099'), ('027','067','091'), (('026','027'),('066','067'),('090','091')), (('027','028'),('075','076'),('099','100')), (('027','028'),('075','076'),('099','100')), ('026','066','090'), (('009','010'),('065','066'),('089','090')),
    # timestamps = [(('009', '010'), ('050', '065'), ('105','090')), (('027', '026'), ('043', '050'), ('098', '091')), (('026', '027'), ('050', '067'), ('091', '090')),
    # timestamps = [
    #     (('026', '027'), ('050', '067'), ('090', '091')),
    #     (('020', '027'), ('043', '060'), ('099', '100')),
    #     ('027', '035', '091'),
    #     ('027', '035', '091'),
    #     ('028', '060', '100'),
    #     (('025', '024'), ('065', '048'), ('104', '105')),
    #     (('025', '026'), ('065', '066'), ('098', '105')) ]
    #('007', '062', '097'), (('004', '007'),
    # case 2 (001, 050, 100) #full three images
    # case 3 (('004', '007'), ('054', '062'), ('094', '097')) #composite

    # ^ punjab
    # tiles = ['42QUM', '42QVM', '42QWM', '42QXM',* '42RTM', '42RTN', '42RTP', '42RTQ', '42RTR', '42RTS', '42RUM', '42RUN', '42RUP', '42RUQ', '42RUR', '42RUS', '42RVM', '42RVN', '42RVP', '42RVQ', '42RVR', '42RVS', '42RWM', '42RWN', '42RWP', '42RWQ', '42RWR', '42RWS', '42RXM', '42RXN', '42RXP', '42RXQ', '42RXR', '42RXS']
    # # ^ sindh
    # timestamps = [
    #     '099',
    #     '099',
    #     (('029', '017'), ('064', '067'), ('102', '104')),
    #     '104',

    # ]

    # tiles = ['42RWT']
    # timestamps = [("007", "067", "097")]
    # Step 1: Search data once with the given parameters
    #append T to all tiles
    # tiles = ["T" + tile for tile in tiles]
    # tiles = ['42QUM', '42QVM', '42QWM', '42QXM', '42RTN', '42RTP', '42RUN', '42RUP', '42RUQ', '42RUR', '42RUS', '42RVN', '42RVP', '42RVQ', '42RVR', '42RVS', '42RWN', '42RWP', '42RWQ', '42RWR', '42RWS', '42RXN', '42RXP', '42RXQ', '42RXR', '42RXS']
    # ^ sindh
    # timestamps = [
    #     '099',
    #     '099',
    #     (('029', '017'), ('064', '067'), ('102', '104')),
    #     '104',
    #     ('005', '065','105'),
    #     '005',
    #     ('007','062','102'),
    #     (('005','007'),('045','047'),('095','099')),
    #     (('005','007'),('072','075'),('100','099')),
    #     (('005','007'),('065','067'),('097','100')),
    #     ('005','065','105'),
    #     ('002','077','102'),
    #     ('007','042','102'),
    #     ('007','067','102'),
    #     ('007','042','097'),
    #     ('007','042','097'),
    #     (('002','004'),('062','064'),('102','104')),
    #     (('007','009'),('062','064'),('102','104')),
    #     ('007','062','102'),
    #     ('007','042','102'),
    #     ('007','067','102'),
    #     '099',
    #     '089',
    #     '104',
    #     '102',
    #     '102'
    # ]

    tiles = ['42RWU', '42RXT', '42RXU', '42RXV', '42RYR', '42RYS', '42RYT', '42RYU', '42RYV', '42SXA', '42SXB', '42SYA', '42SYB', '42SYC', '43RBM', '43RBN', '43RBP', '43RBQ', '43RCN', '43RCP', '43RCQ', '43RDP', '43RDQ', '43SBR', '43SBS', '43SBT', '43SCR', '43SCS', '43SCT', '43SDR', '43SDS', '43SDT', '43SER', '42RWS', '42RXS']
    timestamps = [
    '122',
    (('153', '155'), ('238', '245'), ('353', '355')),
    ('363', '248', '153'),
    ('323', '263', '153'),
    '355',
    ('350','300', '165'),
    ('363', '235', '155'),
    ('360', '285','155'),
    ('360','290','155'),
    ('323', '268', '153'),
    ('363', '263', '153'),
    (('325', '323'), ('270', '268'), ('155', '153')),
    (('348', '340'), ('270', '268'), ('155', '153')),
    ('363', '263', '153'),
    ('350','255', '155'),
    ('350','270', '155'),
    ('360', '265', '155'),
    ('360', '265', '155'),
    (('360', '352'), ('270', '267'), ('157', '155')),
    (('360', '357'), ('277', '275'), ('162', '155')),
    ('360', '265', '155'),
    ('352', '262', '167'),
    ('357', '262', '162'),
    ('360', '265', '155'),
    ('360', '265', '155'),
    (('365', '363'), ('268', '265'), ('155', '153')),
    ('360', '265', '155'),
    ('360', '265', '155'),
    ('360', '265', '155'),
    ('352', '262', '162'),
    (('360', '352'), ('262', '260'), ('162', '155')),
    (('295', '287'), ('257', '255'), ('177', '155')),
    ('352','267', '162'),
    ('363', '268', '153'),
    (('353', '350'), ('268', '265'), ('155', '153'))]

    results = search_hls_data(bounding_box, temporal_range)
    
    if not results:
        print("No results found for the search criteria")
        return None
    
    # Generate a single random name for the output directory
    random_name = generate_random_name()
    output_dir = os.path.join("/home/umer/projects/vector_studio/icons/cropmapping-server-two/mapdata", random_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Store information about all processed tiles
    all_tiles_info = {
        "name": random_name,
        "temporal_range": temporal_range,
        "tiles": []
    }
    
    # Process each tile
    for i, tile_name in enumerate(tiles):
        print(f"Processing tile: {tile_name}", i + 1, "of", len(tiles))
        
        try:
            # Filter results for this specific tile
            filtered_results = filter_results_by_tile(results, tile_name)
            
            if not filtered_results:
                print(f"No results found for tile {tile_name}")
                continue
            
            # Create the map for this tile
            png_path, tiff_path, json_path = create_single_map(filtered_results, tile_name, timestamps[i], output_dir)
            
            if png_path and json_path:
                # Record the tile information
                tile_info = {
                    "tile_name": tile_name,
                    "png_file": os.path.basename(png_path),
                    "json_file": os.path.basename(json_path)
                }
                
                # Add TIFF information if available
                if tiff_path:
                    tile_info["tiff_file"] = os.path.basename(tiff_path)
                    
                all_tiles_info["tiles"].append(tile_info)
                
                # Load the individual tile json to extract bounds for the combined data.json
                with open(json_path, 'r') as f:
                    tile_data = json.load(f)
                    
                # Store the source tiff files used for this tile
                if os.path.exists(json_path):
                    directory = '/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/tiles'
                    tiff_files = [os.path.basename(t) for t in os.listdir(directory) if t.endswith('.tif')]
                    # Update the tile info with the source tiffs
                    tile_info["source_tiffs"] = tiff_files
        except Exception as e:
            print(f"Error processing tile {tile_name}: {str(e)}")
            print(traceback.format_exc())
            print(f"Continuing with the next tile...")
            continue
    
    # Save the master JSON file with information about all tiles
    master_json_path = os.path.join(output_dir, "master.json")
    with open(master_json_path, 'w') as json_file:
        json.dump(all_tiles_info, json_file, indent=4)
    print(f"Saved master JSON to: {master_json_path}")
    
    # Create the combined data.json file
    create_combined_data_json(output_dir, all_tiles_info)
    
    return output_dir

def create_combined_data_json(output_dir, all_tiles_info):
    """Create a combined data.json file containing information about all tile masks."""
    combined_data = {
        "name": "Prithvi Masks",
        "description": f"UNet outputs for multiple tiles ({all_tiles_info['name']})",
        "model": "UNet trained on Prithvi Crop Classification",
        "source": "NASA HLS Sentinel-2 30m",
        "tiles": [],
        "classification_tiffs": {},
        "source_tiffs": {}  # New field to store source TIFF filenames
    }
    
    # Process each tile to add its information to the combined data.json
    for tile_info in all_tiles_info["tiles"]:
        # Read the individual tile's json file to get the bounds
        json_path = os.path.join(output_dir, tile_info["json_file"])
        with open(json_path, 'r') as f:
            tile_data = json.load(f)
        
        # Extract the bounds information and PNG filename
        if tile_data["tiles"] and len(tile_data["tiles"]) > 0:
            tile_entry = tile_data["tiles"][0].copy()
            # Replace just the first element (filename) with the actual png filename
            tile_entry[0] = tile_info["png_file"]
            combined_data["tiles"].append(tile_entry)
            
            # Add TIFF file information if available
            if "tiff_file" in tile_info:
                combined_data["classification_tiffs"][tile_info["tile_name"]] = tile_info["tiff_file"]
            
            # Add source TIFF information if available
            if "source_tiffs" in tile_info:
                combined_data["source_tiffs"][tile_info["tile_name"]] = tile_info["source_tiffs"]
    
    # combined_json_path = os.path.join(output_dir, "data.json")
    # with open(json_path, 'r') as f:
    #     tile_data = json.load(f)
    
    # Save the combined data.json file
    combined_json_path = os.path.join(output_dir, "data.json")
    with open(combined_json_path, 'w') as json_file:
        json.dump(combined_data, json_file, indent=4)
    print(f"Saved combined data.json to: {combined_json_path}")

if __name__ == "__main__":
    # bounding_box = (66.50278, 24.08525, 71.05731, 28.50006) #sindh 
    bounding_box = (69.19673, 27.75666, 75.42023, 33.69635) #punjab
    temporal_range = ("2024-6-1", "2024-12-31")  # Replace with actual date range
    output_dir = create_large_output_map(bounding_box, temporal_range)
    print(f"Output directory: {output_dir}")