from PIL import Image
import os

def stitch256masks(
    input_folder = 'tempData/patches',
    output_file = '???'
):



    # Load all PNG file names from the directory
    png_files = sorted([f for f in os.listdir(input_folder) if f.endswith('.png')])

    # Check if we have 256 files
    if len(png_files) != 256:
        raise ValueError("There should be exactly 256 PNG files in the folder.")

    # Open the first image to determine size (assuming all images have the same dimensions)
    first_image = Image.open(os.path.join(input_folder, png_files[0]))
    image_width, image_height = first_image.size

    # Define the grid size
    grid_size = 16

    # Create a new blank image for the final stitched image
    stitched_image = Image.new('RGBA', (grid_size * image_width, grid_size * image_height))

    # Paste each image into the correct location in the grid
    for index, file_name in enumerate(png_files):
        img = Image.open(os.path.join(input_folder, file_name))
        
        # Calculate the position for the current image in the 16x16 grid
        x_pos = (index % grid_size) * image_width
        y_pos = (index // grid_size) * image_height
        
        # Paste the current image into the stitched image
        stitched_image.paste(img, (x_pos, y_pos))

    # Save the final stitched image
    stitched_image.save(output_file)
    print(f"Stitched image saved as {output_file}")
    return output_file
