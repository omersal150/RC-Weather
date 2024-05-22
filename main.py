from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "337234"
app.config["MONGO_URI"] = "mongodb://mongo:27017/RC-Weather-DB"
mongo = PyMongo(app)

# Function to fetch weather data from Windguru API
def fetch_weather_data(uid, password, station):
    url = "https://www.windguru.cz/int/wgsapi.php"
    params = {
        'uid': uid,
        'password': password,
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
        pass
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
        return render_template('check-weather.html')  # Render the form template for checking weather
    elif request.method == 'POST':
        # Handle POST request
        if 'username' not in session:
            return redirect(url_for('login'))

        # Fetch weather data from Windguru API
        uid = 3372  # Your Windguru UID
        password = 3372  # Your Windguru password
        station = 2049  # Specify the Windguru station ID
        weather_data = fetch_weather_data(uid, password, station)

        if weather_data:
            # Process weather data and store in MongoDB
            # Your code to process weather data and store in MongoDB goes here

            # Redirect to the weather result page
            return redirect(url_for('check_weather_result'))
        else:
            flash('Failed to fetch weather data from Windguru API.', 'error')
            return redirect(url_for('check-weather'))  # Redirect back to the weather form
    else:
        # Handle other HTTP methods
        return 'Method Not Allowed', 405
    
@app.route('/check-weather-result')
def check_weather_result():
    # Placeholder data for demonstration purposes
    weather_data = {
        'datetime': '2024-05-28 12:00',
        'temperature': 25,
        'humidity': 60,
        'wind_speed': 10,
        'wind_direction': 'N'
    }
    return render_template('check_weather_result.html', weather_data=weather_data)

if __name__ == '__main__':
    app.run(debug=True)
