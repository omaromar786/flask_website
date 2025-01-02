# connect to the MongoDB databases and extract data using the functions here
import dash
from pymongo import MongoClient
from datetime import datetime
import json
import requests
from datetime import datetime, timedelta
import pytz

# Initialize Dash app
app = dash.Dash(__name__)

# Function to fetch filtered data from MongoDB
def fetch_filtered_data():
    # Configure MongoDB
    client = MongoClient('mongodb+srv://astspintern:AKaTzHFRyDdeMC2j@trialcluster.dyauzxg.mongodb.net/')
    db = client['UbiBot_Database']
    collection = db['UbiBotData_1']

    # Fetch all data, sorted by timestamp
    cursor = collection.find().sort("timestamp", 1)

    data = {f"field{i}": {"name": "", "x": [], "y": []} for i in range(5, 11)}

    for doc in cursor:
        timestamp = datetime.fromtimestamp(doc["timestamp"])
        for i in range(5, 11):
            field = f"field{i}"
            data[field]["name"] = doc["fields"][field]["name"]
            data[field]["x"].append(timestamp)
            data[field]["y"].append(doc["fields"][field]["last_value"])

    client.close()
    return data

# For Sensors data and Heartbeat data from MongoDB's ESP32 Sensors
def get_latest_data():
    # Configure MongoDB
    client = MongoClient('mongodb+srv://astspintern:AKaTzHFRyDdeMC2j@trialcluster.dyauzxg.mongodb.net/')

    db_esp = client['ESP32_Database']
    sensors_collection = db_esp['ESP32Data_1']

    latest_data = sensors_collection.find_one(sort=[("_id", -1)])
    if latest_data:
        sensors = latest_data["sensors"]
        heartbeats = latest_data["heartbeats"]

        # Handle water_level_percent
        if "water_level_percent" in sensors:
            if sensors["water_level_percent"] is None:
                sensors["water_level_percent"] = 0
            else:
                sensors["water_level_percent"] = round(float(sensors["water_level_percent"]), 2)

        # Handle other potential None values
        for key in sensors:
            if sensors[key] is None:
                sensors[key] = 0

        print(sensors, heartbeats)
        return sensors, heartbeats
    return None, None

# Weather Data

def get_pws_data():
    url = "https://api.weather.com/v2/pws/observations/current?stationId=ISINGA213&format=json&units=m&apiKey=129f96b61bdc40ea9f96b61bdce0ea94"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        return data['observations'][0]
    else:
        return None

def fetch_weather_data():
    client = MongoClient('mongodb+srv://astspintern:AKaTzHFRyDdeMC2j@trialcluster.dyauzxg.mongodb.net/')
    db_weather = client['Weather_Database']
    weather_collection = db_weather['WeatherData_1']

    # Fetch all documents from the collection
    weather_data = list(weather_collection.find())

    # Extract the respective data from each document
    extracted_data = []
    for data in weather_data:
        # Convert timestamp to datetime if it's a float
        if isinstance(data['timestamp'], float):
            timestamp = datetime.fromtimestamp(data['timestamp'])
        else:
            timestamp = data['timestamp']
        
        extracted_data.append({
            'timestamp': timestamp,
            'station_id': data['station_id'],
            'neighborhood': data['neighborhood'],
            'temperature': data['temperature'],
            'feels_like': data['feels_like'],
            'humidity': data['humidity'],
            'dew_point': data['dew_point'],
            'wind_speed': data['wind_speed'],
            'wind_gust': data['wind_gust'],
            'wind_direction': data['wind_direction'],
            'pressure': data['pressure'],
            'uv': data['uv'],
            'solar_radiation': data['solar_radiation']
        })
    
    return extracted_data

# for the table data ubibot
def ubibot_table_data():
    # Configure MongoDB
    client = MongoClient('mongodb+srv://astspintern:AKaTzHFRyDdeMC2j@trialcluster.dyauzxg.mongodb.net/')

    db_ubibot = client['UbiBot_Database']
    ubibot_collection = db_ubibot['UbiBotData_1']

    data = list(ubibot_collection.find({}, {'_id': 1, 'channels.last_values': 1}))

    fields = ['field1', 'field2', 'field3', 'field4', 'field5', 'field6', 'field7', 'field8', 'field9', 'field10']
    field_names = ['PT100 Temperature-T1', 'Humidity', 'Wind Speed', 'WiFi Signal', 'CO2 Probe Temperature', 'Light', 'CO2 Probe Humidity', 'CO2 Probe', 'RS485 Soil Temperature -TH1', 'RS485 Soil Moisture']

    filtered_data = {field: {'x': [], 'y': [], 'id': []} for field in fields}

    for doc in data:
        query_id = str(doc['_id'])
        channels = doc.get('channels', [])
        for channel in channels:
            last_values = json.loads(channel.get('last_values', '{}'))
            for field in fields:
                if field in last_values:
                    filtered_data[field]['x'].append(last_values[field]['created_at'])
                    filtered_data[field]['y'].append(last_values[field]['value'])
                    filtered_data[field]['id'].append(query_id)

    # Convert string timestamps to datetime objects and keep only the last 10 data points
    for field in filtered_data:
        data_points = list(zip(filtered_data[field]['x'], filtered_data[field]['y'], filtered_data[field]['id']))
        data_points.sort(key=lambda x: datetime.fromisoformat(x[0][:-1]))  # Sort by timestamp
        last_10_data_points = data_points[-10:]  # Get the last 10 data points
        
        filtered_data[field]['x'] = [datetime.fromisoformat(x[:-1]) for x, _, _ in last_10_data_points]
        filtered_data[field]['y'] = [y for _, y, _ in last_10_data_points]
        filtered_data[field]['id'] = [id for _, _, id in last_10_data_points]

    # Prepare data for the table
    table_data = {
        'Field': ['ID'] + [item for field in field_names for item in [f'{field} *data', f'{field} *timestamp']]
    }

    for i in range(min(10, len(filtered_data['field1']['id']))):
        col_data = [filtered_data['field1']['id'][i]]
        for field in fields:
            col_data.append(filtered_data[field]['y'][i] if i < len(filtered_data[field]['y']) else '')
            col_data.append(filtered_data[field]['x'][i].strftime('%Y-%m-%d %H:%M:%S') if i < len(filtered_data[field]['x']) else '')
        table_data[f'Data Point {i+1}'] = col_data

    return table_data


def get_weather_data():
    base_url = "https://api.weather.com/v2/pws/observations/current"
    params = {
        "stationId": "ISINGA213",
        "format": "json",
        "units": "m",
        "apiKey": "129f96b61bdc40ea9f96b61bdce0ea94"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if 'observations' not in data or not data['observations']:
            return False, False, False  # Default to "False, False, False" if data is missing

        obs = data['observations'][0]
        
        # Check for cloudiness
        uv_index = obs.get('uv', 0)
        solar_radiation = obs.get('solarRadiation', 0)
        cloudy = uv_index < 3 or solar_radiation < 100

        # Check for rain
        precip_rate = obs.get('metric', {}).get('precipRate', 0)
        raining = precip_rate > 0

        # Check for nighttime using SGT
        singapore_tz = pytz.timezone('Asia/Singapore')
        sg_time = datetime.now(singapore_tz)
        
        # Define nighttime range (7 PM to 7 AM)
        is_night = sg_time.hour >= 19 or sg_time.hour < 7

        # Return results as tuple
        return cloudy, raining, is_night

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return False, False, False  # Default to "False, False, False" in case of error

def get_weather_emoji(cloudy, raining, is_night):
    if is_night:
        return "🌙"
    if raining:
        return "🌧️"
    elif cloudy:
        return "🌤️"  # Changed to partly cloudy emoji
    else:
        return "☀️"
