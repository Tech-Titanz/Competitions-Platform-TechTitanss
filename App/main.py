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
from App.controllers import *


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

        # Fetch the user from the database by username
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:  # Check if user exists and password matches
            session['user'] = user.username  # Store the username in session

            # Flash message for successful login
            flash("Login successful!", "success")

            # Redirect to the appropriate page based on whether the user is a moderator
            if user.is_moderator:
                return redirect(url_for('moderator_dashboard'))  # Redirect to moderator-specific page
            else:
                return redirect(url_for('dashboard'))  # Redirect to default user dashboard
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
        user, error = RegisterUserCommand(username, password)
        
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

@app.route('/moderator_dashboard')
def moderator_dashboard():
    # Only accessible by moderators, so check if the user is a moderator
    if 'user' in session:
        user = User.query.filter_by(username=session['user']).first()
        if user and user.is_moderator:
            return render_template('moderator_dashboard.html', user=user)
        else:
            flash("Access denied. You must be a moderator.", "error")
            return redirect(url_for('login'))  # Redirect non-moderators to login page
    else:
        flash("Please log in to access this page.", "error")
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
