import os
from flask import Flask, render_template
from flask_uploads import DOCUMENTS, IMAGES, TEXT, UploadSet, configure_uploads
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage


from App.database import init_db
from App.config import load_config

from App.database import db
from App.models import Competition


from App.controllers import (
    setup_jwt,
    add_auth_context
)

from App.views import views, setup_admin

def add_views(app):
    for view in views:
        app.register_blueprint(view)

def create_app(overrides={}):
    app = Flask(__name__, static_url_path='/static')
    load_config(app, overrides)
    CORS(app)
    add_auth_context(app)
    photos = UploadSet('photos', TEXT + DOCUMENTS + IMAGES)
    configure_uploads(app, photos)
    add_views(app)
    init_db(app)
    jwt = setup_jwt(app)
    setup_admin(app)
    @jwt.invalid_token_loader
    @jwt.unauthorized_loader
    def custom_unauthorized_response(error):
        return render_template('401.html', error=error), 401
    app.app_context().push()
    return app

from flask import request, redirect, url_for, flash, session

# app = Flask(__name__)
# app = Flask(__name__, static_url_path='/static', template_folder='templates')
app = Flask(__name__, 
            static_url_path='/static', 
            static_folder='App/static', 
            template_folder='App/templates')


app.secret_key = "your_secret_key"

# Dummy user database for demonstration
users = {
    "bob": "bobpass",
    "alice": "alicepass"
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Validate credentials
        if username in users and users[username] == password:
            session['user'] = username
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials. Please try again.", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Use the register_user function to create a new user
        user, error = register_user(username, password)
        
        if error:
            flash(error, "error")  # Show error if username exists
            return redirect(url_for('home'))  # Redirect back to the home page
        else:
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('home'))  # Redirect to home after successful signup

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/leaderboard')
def leaderboard():
    print("Leaderboard route accessed!")
    return render_template('leaderboard.html')

@app.route('/competition_list')
def list():
    return render_template('competition_list.html')

@app.route('/competitions')
def competition_list():
    competitions = Competition.query.all()  # Get all competitions from the database
    return render_template('competition_list.html', competitions=competitions)

if __name__ == '__main__':
    app.run(debug=True)
