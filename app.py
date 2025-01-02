from dash import Dash
from pymongo import MongoClient
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import bcrypt
from app.dash_data import create_dash_layout as data_dash_layout
from app.dash_weather import create_weather_layout as weather_dash_layout
from app.api_routes import api_routes  # Import the Blueprint
import dash_bootstrap_components as dbc
import datetime
import timedelta
import time
import logging

app = Flask(__name__)
app.secret_key = 'efd7a4dc27f3a0d977624fc889c3df97'  # Replace with your secret key

# Initialize Dash app
data_dash_app = Dash(__name__, server=app, url_base_pathname='/data_dash/', 
                     external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css'])
data_dash_layout(data_dash_app)

weather_dash_app = Dash(__name__, server=app, url_base_pathname='/weather_dash/')
weather_dash_layout(weather_dash_app)


# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure MongoDB
client = MongoClient('mongodb+srv://astspintern:AKaTzHFRyDdeMC2j@trialcluster.dyauzxg.mongodb.net/')
db_user = client['Users']
users_collection = db_user['website_users']

db_esp = client['ESP32_Database']
sensors_collection = db_esp['ESP32Data_1']

db_ubibot = client['UbiBot_Database']
ubibot_collection = db_ubibot['UbiBotData_1']

db_VRM = client['VRM_Database']
VRM_collection = db_VRM['VRMData_1']

db_control = client['Control_Database']
light_collection = db_control['LightData']
water_collection = db_control['WaterData']
custom_collection = db_control['CustomData']
option_collection = db_control['WaterOption']
light_auto_select_collection = db_control['LightAutoOption']
light_auto_data_collection = db_control['LightAutoData']
light_custom_collection = db_control['LightCustomData']


notifications = []

@app.route('/') 
def first_page():
    return render_template('home.html')

@app.route('/weather/')
def weather():
    return render_template('weather.html')

@app.route('/login/', methods=['GET'])
def show_login():
    return render_template('login.html')

@app.route('/submit_login/', methods=['POST'])
def submit_login():
    try:
        # Get data from the request
        data = request.json
        username = data.get('username')
        password = data.get('password')

        # Find the user in MongoDB
        user = users_collection.find_one({'username': username})

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'] = username
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout/', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/profile/', methods=['GET'])
def profile():
    if 'username' not in session:
        return redirect(url_for('show_login'))
    
    user = users_collection.find_one({'username': session['username']})
    return render_template('profile.html', user=user)

@app.route('/data/')
def data():
    return render_template('data.html')

'''
Do not allow any more new registerations

@app.route('/register/', methods=['GET'])
def show_register():
    return render_template('register.html')

@app.route('/submit_registration/', methods=['POST'])
def submit_registration():
    try:
        # Get data from the request
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Check if username or email already exists
        if users_collection.find_one({'username': username}):
            return jsonify({'error': 'Username already exists'}), 400
        if users_collection.find_one({'email': email}):
            return jsonify({'error': 'Email already exists'}), 400

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert new user into MongoDB
        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password.decode('utf-8')
        })

        return jsonify({'message': 'Registration successful'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
'''
@app.route('/switch-mode', methods=['POST'])
def switch_mode():
    try:
        # Get the mode from the form
        new_mode = request.form.get('mode')

        # Insert the new mode into MongoDB
        option_collection.insert_one({
            "mode": new_mode,
            "timestamp": datetime.datetime.now().timestamp()
        })

        # Redirect to the appropriate mode page
        if new_mode == "Timer":
            return redirect(url_for('timer_page'))
        else:
            return redirect(url_for('sensor_page'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/mode-switch', methods=['GET'])
def mode_switch():
    try:
        # Fetch the latest mode from MongoDB
        config = option_collection.find_one({"mode": {"$in": ["Timer", "Sensor"]}}, sort=[("timestamp", -1)])
        current_mode = config.get("mode", "Timer") if config else "Timer"

        # Redirect to the corresponding mode page
        if current_mode == "Timer":
            return redirect(url_for('timer_page'))
        else:
            return redirect(url_for('sensor_page'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Timer mode page
@app.route('/timer', methods=['GET'])
def timer_page():
    return render_template('timer.html', current_mode="Timer")

# Sensor mode page
@app.route('/sensor', methods=['GET', 'POST'])
def sensor_page():
    if request.method == 'POST':
        data = request.json
        moisture = data.get('moisture')

        # Validate input
        if not moisture:
            return jsonify({"message": "Moisture value must be provided"}), 400

        try:
            # Convert value to float
            moisture = float(moisture)

            # Insert moisture value into the collection
            timestamp = datetime.datetime.now().timestamp()
            mongo_data = {
                'timestamp': timestamp,
                'moisture': moisture
            }

            # Insert into MongoDB
            custom_collection.insert_one(mongo_data)
            latest_data = custom_collection.find_one(sort=[("timestamp", -1)])

            return jsonify({
                "message": "Request sent successfully",
                "latest_moisture": latest_data.get('moisture') if latest_data else None
            }), 200

        except ValueError:
            return jsonify({"message": "Invalid data format"}), 400

    # Fetch the latest document
    latest_data = custom_collection.find_one(sort=[("timestamp", -1)])
    return render_template('sensor.html', current_mode="Sensor", latest_data=latest_data)

@app.route('/sensor/latest', methods=['GET'])
def get_latest_set_moisture():
    # Fetch the latest document from the database
    latest_data = custom_collection.find_one(sort=[("timestamp", -1)])
    if latest_data:
        return jsonify({
            "latest_moisture": latest_data.get('moisture')
        }), 200
    return jsonify({
        "latest_moisture": None
    }), 200


@app.route('/latest_moisture', methods=['GET'])
def get_latest_moisture():
    try:
        # Find the latest document sorted by '_id' or timestamp field
        latest_document = sensors_collection.find_one({}, sort=[('_id', -1)])

        if latest_document and 'sensors' in latest_document:
            sensors = latest_document['sensors']
            
            # Extract values
            soil_moisture = sensors.get('soil_moisture', None)
            water_level_percent = sensors.get('water_level_percent', None)
            
            # Check if either value is missing
            if soil_moisture is not None and water_level_percent is not None:
                return jsonify({
                    'moisture': soil_moisture,
                    'water_level_percent': water_level_percent
                })
            else:
                missing_fields = []
                if soil_moisture is None:
                    missing_fields.append('soil_moisture')
                if water_level_percent is None:
                    missing_fields.append('water_level_percent')
                return jsonify({'error': f'{", ".join(missing_fields)} field(s) not found'}), 404
        else:
            return jsonify({'error': 'No documents found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stop', methods=['POST'])
def stop_action():
    try:
        # Parse the JSON data from the request
        data = request.json
        if not data or 'action' not in data:
            return jsonify({"status": "error", "message": "Invalid request, 'action' field is required"}), 400
        
        # Extract the action field
        action_value = data['action']
        
        # Insert the action into the database
        document = {"action": action_value,
                    "timestamp": datetime.datetime.now().timestamp() 
                    }
        water_collection.insert_one(document)
        
        # Return a success response
        return jsonify({"status": "success", "message": "Action recorded successfully"}), 200
    except Exception as e:
        # Handle errors
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/control/')
def control():
    return render_template('control.html')

@app.route('/current_light_state', methods=['GET'])
def current_light_state():
    """
    Fetch the latest On/Off state exclusively from light_collection (Collection B).
    """
    try:
        pipeline = [
            {"$match": {"action": {"$in": ["On", "Off"]}}},
            {"$sort": {"timestamp": -1}},
            {"$limit": 1}
        ]
        result = list(light_collection.aggregate(pipeline))
        current_action = result[0].get("action", "Off") if result else "Off"
        return jsonify({"action": current_action})
    except Exception as e:
        print("Error fetching light state:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/current_state', methods=['GET'])
def current_state():
    """
    Fetch the latest 'On' or 'Off' state from light_collection.
    """
    try:
        pipeline = [
            {"$match": {"action": {"$in": ["On", "Off"]}}},
            {"$sort": {"timestamp": -1}},
            {"$limit": 1}
        ]
        result = list(light_collection.aggregate(pipeline))
        current_action = result[0].get("action", "Off") if result else "Off"
        return jsonify({"action": current_action})
    except Exception as e:
        print("Error fetching current state:", e)
        return jsonify({"error": str(e)}), 500



@app.route('/update_state', methods=['POST'])
def update_state():
    """
    Update the 'On' or 'Off' state in light_collection.
    """
    try:
        data = request.get_json()
        action = data.get('action')

        if action in ['On', 'Off']:
            document = {
                "action": action,
                "timestamp": datetime.datetime.now().timestamp()
            }
            light_collection.insert_one(document)
            return jsonify({"message": f"State updated to {action}"})
        else:
            return jsonify({"message": "Invalid action"}), 400
    except Exception as e:
        print("Error updating state:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/auto_state', methods=['GET', 'POST'])
def auto_state():
    """
    GET: Fetch the latest auto state.
    POST: Update the auto state to 'Yes' or 'No'.
    """
    if request.method == 'POST':
        data = request.get_json()
        auto_value = data.get('auto')

        if auto_value in ['Yes', 'No']:
            light_auto_select_collection.insert_one({
                "auto": auto_value,
                "timestamp": datetime.datetime.now().timestamp()
            })
            return jsonify({"message": f"Auto state updated to {auto_value}"})
        else:
            return jsonify({"message": "Invalid auto state"}), 400

    # Fetch the latest auto state
    latest_auto = light_auto_select_collection.find_one(sort=[("timestamp", -1)])
    current_auto = latest_auto['auto'] if latest_auto else "No"
    return jsonify({"auto": current_auto})

@app.route('/light_status', methods=['GET'])
def light_status():
    """
    Fetch the current light status:
    - Check 'auto' field in light_auto_select_collection.
    - If 'auto' == 'Yes', fetch from light_auto_data_collection (Collection A).
    - If 'auto' == 'No', fetch from light_collection (Collection B).
    """
    try:
        # Step 1: Check the latest 'auto' field from light_auto_select_collection
        latest_auto_doc = light_auto_select_collection.find_one(sort=[("timestamp", -1)])
        auto_mode = latest_auto_doc.get('auto', 'No') if latest_auto_doc else 'No'

        # Step 2: Determine the collection to fetch 'action' field
        target_collection = light_auto_data_collection if auto_mode == 'Yes' else light_collection

        # Step 3: Fetch the latest 'action' document from the target collection
        pipeline = [
            {"$match": {"action": {"$in": ["On", "Off"]}}},  # Filter valid actions
            {"$sort": {"timestamp": -1}},  # Sort by latest timestamp
            {"$limit": 1}  # Get the most recent document
        ]
        result = list(target_collection.aggregate(pipeline))
        action = result[0].get("action", "Off") if result else "Off"

        # Step 4: Return the action for the light bulb
        return jsonify({"action": action})
    except Exception as e:
        print("Error fetching light status:", e)
        return jsonify({"error": str(e)}), 500
    
@app.route('/submit_illumination', methods=['POST'])
def submit_illumination():
    """
    Submit an illumination value to the illumination_collection.
    """
    try:
        data = request.get_json()
        illumination_value = int(data.get('illumination'))

        if illumination_value >= 0:  # Adjust the range validation as needed
            light_custom_collection.insert_one({
                "illumination_needed": illumination_value,
                "timestamp": datetime.datetime.now().timestamp()
            })
            return jsonify({"message": f"Illumination level {illumination_value} submitted successfully."})
        else:
            return jsonify({"message": "Illumination value must be a positive number."}), 400
    except Exception as e:
        print("Error submitting illumination value:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/latest_illumination', methods=['GET'])
def get_latest_illumination():
    try:
        # Fetch the latest document
        latest_document = ubibot_collection.find_one({}, sort=[("timestamp", -1)])
        illumination_value = 0
        if latest_document and "fields" in latest_document:
            for field in latest_document["fields"].values():
                if field.get("name") == "Illumination":
                    illumination_value = field.get("last_value", 0)
                    break
        return jsonify({"illumination": illumination_value})
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Failed to fetch illumination value"}), 500
    
@app.route('/fetch_set_illumination', methods=['GET'])
def fetch_latest_set_illumination():
    """
    Endpoint to retrieve the latest document's 'illumination_needed' field.
    """
    latest_document = light_custom_collection.find_one(sort=[("timestamp", -1)])  # Get the latest document by timestamp
    if latest_document and 'illumination_needed' in latest_document:
        return jsonify({'illumination_needed': latest_document['illumination_needed']})
    return jsonify({'error': 'No document found'}), 404

@app.route('/get_VRM_data')
def get_data():
    data = list(VRM_collection.find({}, {"_id": 0}))  # Fetch all documents without ObjectId
    for entry in data:
        # Convert UNIX timestamp to human-readable format
        entry["formatted_time"] = datetime.datetime.utcfromtimestamp(entry["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(data)

@app.route('/VRM')
def index():
    return render_template("VRM.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
