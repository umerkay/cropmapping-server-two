from flask import Blueprint, jsonify, request, send_from_directory, abort
import os
import json

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
