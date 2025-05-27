import rasterio
import numpy as np
from PIL import Image
import os

def read_and_normalize_band(band_data, clip_percent=(2, 98)):
    band = band_data.astype(np.float32)
    p2, p98 = np.percentile(band, clip_percent)
    band = np.clip((band - p2) / (p98 - p2), 0, 1)
    band = (band * 255).astype(np.uint8)
    return band

# Path to the multi-band TIFF file
multi_band_tiff_path = '/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/patches/patch_23.tif'

# Output directory for grayscale images
output_dir = 'bandspng'
os.makedirs(output_dir, exist_ok=True)

# Read the multi-band file
with rasterio.open(multi_band_tiff_path) as src:
    num_bands = src.count
    for i in range(1, num_bands + 1):
        band_data = src.read(i)
        band_img = read_and_normalize_band(band_data)
        img = Image.fromarray(band_img)
        img.save(os.path.join(output_dir, f'band_{i:02}.png'))

print(f"Saved {num_bands} grayscale images to {output_dir}")
