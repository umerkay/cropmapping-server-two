import rasterio

def read_tiff_band_stats(tiff_path):
    with rasterio.open(tiff_path) as src:
        print(f"File: {tiff_path}")
        print(f"Width: {src.width}, Height: {src.height}")
        print(f"Number of bands: {src.count}")
        print(f"CRS: {src.crs}")
        print("")

        for i in range(1, src.count + 1):  # Bands are 1-indexed in rasterio
            band = src.read(i)
            band_min = band.min()
            band_max = band.max()
            print(f"Band {i}: min = {band_min}, max = {band_max}")

# Example usage
read_tiff_band_stats("/home/umer/projects/vector_studio/icons/cropmapping-server-two/tempData/tiles/HLS.S30.T42RXT.2025004T055231.v2.0.B02.tif")
