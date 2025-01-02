from flask import Blueprint, jsonify, request
from pymongo import MongoClient
from datetime import datetime

# Define a Flask Blueprint
api_routes = Blueprint('api_routes', __name__)

# MongoDB setup
client = MongoClient('mongodb+srv://astspintern:AKaTzHFRyDdeMC2j@trialcluster.dyauzxg.mongodb.net/')  # Replace with your connection string
db_control = client['Control_Database']
option_collection = db_control['WaterOption']

# Fetch the current mode document from MongoDB
@api_routes.route('/api/get-mode', methods=['GET'])
def get_mode():
    try:
        # Query the latest document with "Timer" or "Sensor" mode
        config = option_collection.find_one({"mode": {"$in": ["Timer", "Sensor"]}})
        if config:
            return jsonify({"mode": config.get("mode")})
        return jsonify({"mode": "Timer"})  # Default to "Timer" if no document is found
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Update the mode in MongoDB (creates a new document with the new mode)
@api_routes.route('/api/set-mode', methods=['POST'])
def set_mode():
    try:
        data = request.get_json()
        new_mode = data.get("mode")
        if new_mode not in ["Timer", "Sensor"]:
            return jsonify({"error": "Invalid mode"}), 400

        # Create a new document for the new mode
        option_collection.insert_one({
            "mode": new_mode,
            "timestamp": datetime.now().timestamp()  # Store the timestamp of the mode change
        })
        return jsonify({"message": "Mode switched successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500