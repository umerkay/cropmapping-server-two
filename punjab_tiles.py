import geopandas as gpd
from shapely.geometry import box
from mgrs import MGRS

# Load Punjab GeoJSON
punjab = gpd.read_file("sindh.json")

# Define bounding box over Punjab
minx, miny, maxx, maxy = punjab.total_bounds

# MGRS object
m = MGRS()

# Step through lat/lon grid (e.g., every ~0.5° is ~50km, good enough for 100km tiles)
tiles = set()
lat_step = 0.5
lon_step = 0.5
lat = miny
while lat <= maxy:
    lon = minx
    while lon <= maxx:
        mgrs_code = m.toMGRS(lat, lon, MGRSPrecision=0)  # 100km tile
        tiles.add(mgrs_code)
        lon += lon_step
    lat += lat_step

# Optional: convert tile codes to geometries and intersect with punjab shape
print(sorted(tiles))
