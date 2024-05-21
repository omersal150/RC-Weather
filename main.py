from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash  # Import check_password_hash

app = Flask(__name__)
app.secret_key = "337234"
app.config["MONGO_URI"] = "mongodb://localhost:27017/myDatabase"
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
        # Handle form submission and database insertion
        # Redirect user upon successful registration
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

if __name__ == '__main__':
    app.run(debug=True)