from flask import Flask, jsonify
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
    # Load the geojson file containing your polygons
    with open('districts.json', 'r') as f:
        geojson_data = json.load(f)

    # Extract the names of the polygons (district names are in "NAME_3")
    polygons = [
        {"name": feature["properties"]["NAME_3"], "id": feature["properties"]["GID_3"]}
        for feature in geojson_data["features"]
    ]
    
    return jsonify({"polygons": polygons, "geojson": geojson_data})

if __name__ == '__main__':
    app.run(debug=True)
