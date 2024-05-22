from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "337234"
app.config["MONGO_URI"] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/RC-Weather-DB')
mongo = PyMongo(app)

# Define a mapping of RC fields to station IDs
rc_field_station_mapping = {
    'Field1': 2049,  # Replace with actual station IDs
    'Field2': 2049,
    'Field3': 757,
    'Field4': 1164331
}

# Function to fetch weather data from Windguru API
def fetch_weather_data(uid, password, station):
    url = "https://www.windguru.cz/int/wgsapi.php"
    params = {
        'uid': 3372,
        'password': 3372,
        'q': 'station_data_current',
        'format': 'json',
        'station': station  # Specify the station ID
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))  # Redirect to home page if logged in
    return render_template('index.html')  # Render index page if not logged in

@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password, method='sha256')

        user = {
            'email': email,
            'password': hashed_password
        }

        mongo.db.users.insert_one(user)
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = mongo.db.users.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            session['username'] = user['email']  # Store email as username
            return redirect(url_for('home'))  # Redirect to home page upon successful login
        else:
            flash('Invalid email/password combination.', 'error')
            return render_template('login.html')

    # If it's a GET request, simply render the login page
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/check-weather', methods=['GET', 'POST'])
def check_weather():
    if request.method == 'GET':
        # Handle GET request
        return render_template('check-weather.html')  # Render form template for checking weather
    elif request.method == 'POST':
        # Handle POST request
        if 'username' not in session:
            return redirect(url_for('login'))

        # Fetch weather data from Windguru API
        uid = 3372  # Your Windguru UID
        password = 3372  # Your Windguru password
        rc_field = request.form.get('rc-field')
        station = rc_field_station_mapping.get(rc_field)  # Get the station ID based on the RC field

        weather_data = fetch_weather_data(uid, password, station)

        if weather_data:
            date_time_str = request.form.get('datetime')
            if date_time_str:
                date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')

                # Store weather check information in MongoDB
                weather_check = {
                    'username': session['username'],
                    'date_time': date_time,
                    'rc_field': rc_field,
                    'rc_model': request.form.get('rc-model'),
                    'wind_speed': weather_data['station_data']['LAST']['wind_avg'] if 'station_data' in weather_data and 'LAST' in weather_data['station_data'] else 0,
                    'wind_direction': weather_data['station_data']['LAST']['wind_direction'] if 'station_data' in weather_data and 'LAST' in weather_data['station_data'] else 0,
                    'result': 'Weather data fetched successfully'
                }
                mongo.db.UserLogs.insert_one(weather_check)

                # Render template with weather check result
                return render_template('check_weather_result.html', weather_data=weather_check)
            else:
                flash('Date and time are required.', 'error')
                return redirect(url_for('check_weather'))
        else:
            flash('Failed to fetch weather data from Windguru API.', 'error')
            return redirect(url_for('check_weather'))
    else:
        # Handle other HTTP methods
        return 'Method Not Allowed', 405

@app.route('/past_weather')
def past_weather():
    # Your logic for handling past weather data goes here
    return 'Past Weather Data'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
