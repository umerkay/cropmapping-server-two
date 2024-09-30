from flask import Flask
from api.routes.map import map_bp
from flask_cors import CORS  # Import CORS from flask_cors

app = Flask(__name__)

# Enable CORS for the entire app
CORS(app)

# Register the blueprint for map-related routes
app.register_blueprint(map_bp)

if __name__ == '__main__':
    app.run(debug=True)
