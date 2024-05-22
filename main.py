import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

def fetch_weather_data(uid, password):
    url = "https://www.windguru.cz/int/wgsapi.php"
    params = {
        'uid': uid,
        'password': password,
        'q': 'station_data_current',
        'format': 'json'
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

app = Flask(__name__)
app.secret_key = "337234"
app.config["MONGO_URI"] = "mongodb://mongo:27017/RC-Weather-DB"
mongo = PyMongo(app)

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
        birthday = request.form.get('birthday')

        existing_user = mongo.db.users.find_one({'email': email})

        if existing_user is None:
            hashed_password = generate_password_hash(password)
            mongo.db.users.insert_one({
                'email': email,
                'password': hashed_password,
                'birthday': birthday
            })
            return redirect(url_for('login'))
        else:
            flash('User already exists!', 'error')
            return render_template('register.html')

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

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/check-weather', methods=['POST'])
def check_weather():
    rc_field = request.form.get('rc-field')
    rc_model = request.form.get('rc-model')
    datetime_str = request.form.get('datetime')
    user_email = session.get('username')

    # Fetch weather data from Windguru API
    windguru_uid = "your_windguru_uid"
    windguru_password = "your_windguru_password"

    weather_data = fetch_weather_data(windguru_uid, windguru_password)

    if weather_data:
        # Parse datetime if available
        weather_datetime = weather_data.get('datetime', '')
        if weather_datetime:
            try:
                current_time = datetime.strptime(weather_datetime, '%Y-%m-%d %H:%M:%S %Z')
            except ValueError:
                current_time = None
        else:
            current_time = None

        if current_time:
            conditions = "Ideal" if is_ideal_conditions(weather_data) else "Not Ideal"
        else:
            conditions = "Weather data not available"
    else:
        conditions = "Failed to fetch weather data"

    # Save the search in the database
    mongo.db.weather_searches.insert_one({
        'user': user_email,
        'rc_field': rc_field,
        'rc_model': rc_model,
        'datetime': datetime_str,
        'conditions': conditions
    })

    flash(f'Weather conditions: {conditions}', 'success')
    return redirect(url_for('home'))


@app.route('/past-weather')
def past_weather():
    if 'username' in session:
        # Retrieve past searches from the database
        searches = list(mongo.db.weather_searches.find({'user': session['username']}))
        return render_template('past-weather.html', searches=searches)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
