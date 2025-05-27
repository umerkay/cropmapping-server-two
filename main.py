from flask import Flask, jsonify, request
import json
from api.routes.map import map_bp
from flask_cors import CORS  # Import CORS from flask_cors

app = Flask(__name__)

# Enable CORS for the entire app
CORS(app)

# Register the blueprint for map-related routes
app.register_blueprint(map_bp)

@app.route('/api/geojson', methods=['GET'])
def get_geojson():
    # Get the 'level' query parameter from the request
    level = request.args.get('level', 'districts')  # Default to 'districts' if no level is provided
    
    # Determine the file to read based on the level
    if level == 'provinces':
        file_name = 'provinces.json'
    elif level == 'all':
        file_name = 'all.json'
    else:
        file_name = 'districts.json'

    # Load the geojson file
    try:
        with open(file_name, 'r') as f:
            geojson_data = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": f"{file_name} not found"}), 404

    # Extract the names of the polygons (district or province names in "NAME_3" or "NAME_1" depending on the level)
    polygons = [
        {"name": feature["properties"].get("NAME_1" if level == 'provinces' else "NAME_3"),
         "id": feature["properties"].get("GID_1" if level == 'provinces' else "GID_3")}
        for feature in geojson_data["features"]
    ]
    
    return jsonify({"polygons": polygons, "geojson": geojson_data})

if __name__ == '__main__':
    #port 5091
    app.run(host='0.0.0.0', port=5091, debug=True)
