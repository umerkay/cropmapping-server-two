import rasterio
import numpy as np
from PIL import Image

def read_and_normalize_band(path, clip_percent=(2, 98)):
    with rasterio.open(path) as src:
        band = src.read(1).astype(np.float32)
        p2, p98 = np.percentile(band, clip_percent)
        band = np.clip((band - p2) / (p98 - p2), 0, 1)
        band = (band * 255).astype(np.uint8)
        return band

# Paths to your HLS S30 bands (adjust filenames accordingly)
red_band_path = '/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/tiles/composites/HLS.S30.T42RXT.composite_0_B04.tif'   # Red
green_band_path = '/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/tiles/composites/HLS.S30.T42RXT.composite_0_B03.tif' # Green
blue_band_path = '/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/tiles/composites/HLS.S30.T42RXT.composite_0_B02.tif'  # Blue

# Read and normalize bands
red = read_and_normalize_band(red_band_path)
green = read_and_normalize_band(green_band_path)
blue = read_and_normalize_band(blue_band_path)

# Stack as RGB and save
rgb = np.stack([red, green, blue], axis=-1)
img = Image.fromarray(rgb)
img.save('hls_rgb.png')
