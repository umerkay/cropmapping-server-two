from flask import Blueprint, jsonify, request, send_from_directory, abort
import os
import json
from pyproj import Transformer
from ..util.createOutputMap import create_map  # Assuming create_map is in a separate module

# Create a blueprint for the map endpoints
map_bp = Blueprint('map', __name__, url_prefix='/map')

# Path to the mapdata folder
MAPDATA_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mapdata')

# Route to list timestamps (folders inside mapdata)
@map_bp.route('/timestamps', methods=['GET'])
def get_timestamps():
    try:
        # List directories in the mapdata folder
        timestamps = [d for d in os.listdir(MAPDATA_FOLDER) if os.path.isdir(os.path.join(MAPDATA_FOLDER, d))]
        return jsonify(timestamps)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get tileinfo (data.json) for a given timestamp
@map_bp.route('/tileinfo', methods=['GET'])
def get_tileinfo():
    timestamp = request.args.get('timestamp')
    if not timestamp:
        return jsonify({"error": "timestamp parameter is required"}), 400

    timestamp_folder = os.path.join(MAPDATA_FOLDER, timestamp)
    data_file = os.path.join(timestamp_folder, 'data.json')

    if not os.path.exists(timestamp_folder) or not os.path.isdir(timestamp_folder):
        return jsonify({"error": "Timestamp folder not found"}), 404

    if not os.path.exists(data_file):
        return jsonify({"error": "data.json not found"}), 404

    # Return the contents of data.json
    with open(data_file, 'r') as f:
        data = json.load(f)
    return jsonify(data)

# Serve static files from the mapdata folder
@map_bp.route('/data/<path:filepath>', methods=['GET'])
def serve_mapdata(filepath):
    try:
        # Serve the requested file from the mapdata folder
        return send_from_directory(MAPDATA_FOLDER, filepath)
    except FileNotFoundError:
        abort(404, description="File not found")

# Route to generate a tile with the given bounding box and fixed temporal range
@map_bp.route('/generate', methods=['POST'])
def generate_tile():
    # try:
    # Get the bounding box from the request body
    bbox = request.json.get('bounding_box')
    if not bbox or len(bbox) != 4:
        return jsonify({"error": "bounding_box parameter is required and should contain four values"}), 400

    # Convert bounding box from WGS84 (EPSG:4326) to EPSG:32643
    # transformer = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    # minx, miny = transformer.transform(bbox[0], bbox[1])
    # maxx, maxy = transformer.transform(bbox[2], bbox[3])

    # Prepare the bounding box in EPSG:32643 format
    # transformed_bbox = [minx, miny, maxx, maxy]

    # Temporal range (fixed for this example)
    temporal_range = ("2023-04-01", "2023-12-01")

    # Call the create_map function to generate the tile
    output_png, output_json = create_map(bbox, temporal_range)

    # Return the tile name (using the folder name created by create_map)
    tile_name = os.path.basename(os.path.dirname(output_png))
    return jsonify({"tile_name": tile_name, "output_png": output_png, "output_json": output_json})

    # except Exception as e:
        # return jsonify({"error": str(e)}), 500
