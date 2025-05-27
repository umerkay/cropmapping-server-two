from PIL import Image
import os
import re
import numpy as np
import tifffile
import rasterio
from rasterio.transform import Affine
from copy import copy
import glob

def stitch256masks(
    input_folder = '/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/patches_masks',
    output_file = '/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/finalOutput/stiched_image.png',
    rgb_masks=None,
    class_masks=None
):
    # Check if output folder exists, create if not
    output_dir = os.path.dirname(output_file)
    os.makedirs(output_dir, exist_ok=True)
    
    # Define output paths for both PNG and TIFF
    output_tiff = output_file.replace('.png', '.tiff')
    
    # Function to extract the numeric part from the filename
    def extract_number(filename):
        match = re.search(r'(\d+)', filename)  # Find the first occurrence of digits in the filename
        return int(match.group()) if match else 0  # Return the number if found, otherwise return 0

    # Define the grid size
    grid_size = 16
    
    if rgb_masks is not None and class_masks is not None:
        # Use masks directly from memory
        print("Using masks from memory for stitching")
        
        # Get dimensions from the first mask
        image_height, image_width, _ = rgb_masks[0].shape
        tiff_height, tiff_width = class_masks[0].shape
        
        # Create a new blank image for the final stitched PNG
        stitched_image_array = np.zeros((grid_size * image_height, grid_size * image_width, 4), dtype=np.uint8)
        stitched_image_array[:,:,3] = 255  # Set alpha channel to fully opaque
        
        # Create a new numpy array for the stitched TIFF
        stitched_tiff = np.zeros((grid_size * tiff_height, grid_size * tiff_width), dtype=np.uint8)
        
        # Paste each mask into the correct location in the grid
        for index in range(min(len(rgb_masks), len(class_masks), 256)):
            # Calculate positions
            x_pos = (index % grid_size) * image_width
            y_pos = (index // grid_size) * image_height
            tiff_x = (index % grid_size) * tiff_width
            tiff_y = (index // grid_size) * tiff_height
            
            # Place the RGB mask into the stitched array
            stitched_image_array[y_pos:y_pos + image_height, x_pos:x_pos + image_width, :3] = rgb_masks[index]
            
            # Place the TIFF data into the stitched array
            stitched_tiff[tiff_y:tiff_y + tiff_height, tiff_x:tiff_x + tiff_width] = class_masks[index]
        
        # Convert to PIL image for saving
        stitched_image = Image.fromarray(stitched_image_array, 'RGBA')
        
    else:
        # Fall back to reading from files if no memory arrays are provided
        print("Reading masks from disk for stitching")
        
        # Get list of PNG files and sort them based on the numeric part
        png_files = sorted([f for f in os.listdir(input_folder) if f.endswith('_mask.png')],
                        key=extract_number)
        
        # Get list of class TIFF files and sort them
        tiff_files = sorted([f for f in os.listdir(input_folder) if f.endswith('_class.tif')],
                         key=extract_number)
        
        print(f"Found {len(png_files)} PNG files and {len(tiff_files)} TIFF files")
        
        # Check if we have 256 files for each type
        if len(png_files) != 256 or len(tiff_files) != 256:
            print(f"Warning: Expected 256 files but found {len(png_files)} PNGs and {len(tiff_files)} TIFFs")
        
        # Open the first image to determine size
        first_image = Image.open(os.path.join(input_folder, png_files[0]))
        image_width, image_height = first_image.size
        
        # Also get dimensions for the TIFF
        first_tiff = tifffile.imread(os.path.join(input_folder, tiff_files[0]))
        tiff_height, tiff_width = first_tiff.shape
        
        # Create a new blank image for the final stitched PNG
        stitched_image = Image.new('RGBA', (grid_size * image_width, grid_size * image_height))
        
        # Create a new numpy array for the stitched TIFF
        stitched_tiff = np.zeros((grid_size * tiff_height, grid_size * tiff_width), dtype=np.uint8)
        
        # Paste each image into the correct location in the grid
        for index, file_name in enumerate(png_files):
            # Process PNG
            img = Image.open(os.path.join(input_folder, file_name))
            
            # Calculate the position for the current image in the 16x16 grid
            x_pos = (index % grid_size) * image_width
            y_pos = (index // grid_size) * image_height
            
            # Paste the current image into the stitched image
            stitched_image.paste(img, (x_pos, y_pos))
            
            # Process corresponding TIFF
            tiff_name = tiff_files[index]
            tiff_data = tifffile.imread(os.path.join(input_folder, tiff_name))
            
            # Calculate the position for the TIFF
            tiff_x = (index % grid_size) * tiff_width
            tiff_y = (index // grid_size) * tiff_height
            
            # Place the TIFF data into the stitched array
            stitched_tiff[tiff_y:tiff_y + tiff_height, tiff_x:tiff_x + tiff_width] = tiff_data
    
    # Save the final stitched PNG image
    stitched_image.save(output_file)
    print(f"Stitched PNG image saved as {output_file}")
    
    # Find the original georeferenced TIFF to copy metadata
    source_tifs = glob.glob('/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/tiles/*.tif')
    if source_tifs:
        # Use the first TIFF file to get georeference information
        with rasterio.open(source_tifs[0]) as src:
            # Copy the metadata
            out_meta = copy(src.meta)
            
            # Calculate the new transform for the larger stitched image
            # We need to adjust the transform to account for the upscaling to a 16x16 grid
            src_transform = src.transform
            
            # Create a new transform with adjusted resolution
            new_transform = Affine(
                src_transform.a / (grid_size * tiff_width / src.width),  # Scale the pixel width
                src_transform.b,
                src_transform.c,  # x_min coordinate stays the same
                src_transform.d,
                src_transform.e / (grid_size * tiff_height / src.height),  # Scale the pixel height
                src_transform.f   # y_max coordinate stays the same
            )
            
            # Update the metadata with the new dimensions and transform
            out_meta.update({
                'height': stitched_tiff.shape[0],
                'width': stitched_tiff.shape[1],
                'transform': new_transform,
                'dtype': 'uint8',
                'count': 1,  # Single band for class values
                'nodata': 255  # Use 255 as nodata value for uint8, as it's within the valid range
            })
            
            # Write the stitched TIFF with georeference information
            with rasterio.open(output_tiff, 'w', **out_meta) as dest:
                dest.write(stitched_tiff, 1)
                print(f"Stitched georeferenced TIFF saved as {output_tiff}")
    else:
        # If no source TIFF was found, save without georeference
        print("Warning: No source GeoTIFF found for georeference metadata")
        tifffile.imwrite(output_tiff, stitched_tiff)
        print(f"Stitched TIFF (without georeference) saved as {output_tiff}")
    
    return output_file

if __name__ == "__main__":
    # Example usage
    stitch256masks()