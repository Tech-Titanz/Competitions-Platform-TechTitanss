# import os

# def load_config(app, overrides):
#     if os.path.exists(os.path.join('./App', 'custom_config.py')):
#         app.config.from_object('App.custom_config')
#     else:
#         app.config.from_object('App.default_config')
#     app.config.from_prefixed_env()
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     app.config['TEMPLATES_AUTO_RELOAD'] = True
#     app.config['PREFERRED_URL_SCHEME'] = 'https'
#     app.config['UPLOADED_PHOTOS_DEST'] = "App/uploads"
#     app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
#     app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
#     app.config["JWT_COOKIE_SECURE"] = True
#     app.config["JWT_COOKIE_CSRF_PROTECT"] = False
#     app.config['FLASK_ADMIN_SWATCH'] = 'darkly'
#     for key in overrides:
#         app.config[key] = overrides[key]

import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize the SQLAlchemy and Migrate instances
db = SQLAlchemy()

def load_config(app, overrides):
    # Check if custom configuration exists
    if os.path.exists(os.path.join('./App', 'custom_config.py')):
        app.config.from_object('App.custom_config')
    else:
        # Load the default configuration if custom_config doesn't exist
        app.config.from_object('App.default_config')

    # Additional configurations (these can be adjusted based on your needs)
    app.config.from_prefixed_env()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['UPLOADED_PHOTOS_DEST'] = "App/uploads"
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
    app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
    app.config["JWT_COOKIE_SECURE"] = True
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    app.config['FLASK_ADMIN_SWATCH'] = 'darkly'

    # Override any specific configuration passed in `overrides`
    for key in overrides:
        app.config[key] = overrides[key]

def get_migrate(app):
    # Initialize Flask-Migrate with the app and db instance
    return Migrate(app, db)

def create_db():
    # Create all tables defined in the models
    db.create_all()

def init_db(app):
    # Initialize the db with the app
    db.init_app(app)
