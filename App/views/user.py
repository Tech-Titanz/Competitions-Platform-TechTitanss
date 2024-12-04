from flask import Blueprint, render_template, jsonify, request, send_from_directory, flash, redirect, session, url_for
from flask_jwt_extended import jwt_required, current_user as jwt_current_user
from sqlalchemy.exc import IntegrityError
from App.controllers.commands import ViewProfileCommand
from App.database import db
from.index import index_views
from App.models import *

from App.controllers import (
    create_user,
    get_all_users,
    get_all_users_json,
    jwt_required
)

user_views = Blueprint('user_views', __name__, template_folder='../templates')

@user_views.route('/users', methods=['GET'])
def get_user_page():
    users = get_all_users()
    return render_template('users.html', users=users)

@user_views.route('/users', methods=['POST'])
def create_user_action():
    data = request.json  
    username = data.get('username')
    password = data.get('password')

 
    if not username or not password:
        return jsonify({'error': 'Username and password are required!'}), 400

   
    try:
        user = create_user(username, password)  
    except IntegrityError:
        return jsonify({'error': 'Username already exists!'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    flash(f"User {username} created!")

    return jsonify({'message': f'User created with id {user.id}'}), 201

@user_views.route('/api/users', methods=['GET'])
def get_users_action():
    users = get_all_users_json()
    return jsonify(users)

@user_views.route('/api/users', methods=['POST'])
def create_user_endpoint():
    data = request.json
    user = create_user(data['username'], data['password'])
    return jsonify({'message': f"user {user.username} created with id {user.id}"})

@user_views.route('/static/users', methods=['GET'])
def static_user_page():
  return send_from_directory('static', 'static-user.html')


@user_views.route('/register',methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    existing_user = User.query.filer_by(username=username).first()
    if existing_user:
        return jsonify({"message": "Username already taken"}), 400
    
    new_user = User(username=username,password=password,is_moderator=False)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully!"}), 201

# routes.py

@user_views.route('/profile', methods=['GET'])
def view_profile():
    user_id = session.get('user_id') 

    command = ViewProfileCommand(user_id)
    profile_details = command.execute()

    if isinstance(profile_details, tuple): 
        flash(profile_details[0], 'error')
        return redirect(url_for('auth_views.login_page'))

    # Unpack profile details
    username = profile_details["username"]
    rank = profile_details["rank"]
    competitions = profile_details["competitions"]

    return render_template('view_profile(m).html', 
                           username=username, 
                           rank=rank, 
                           competitions=competitions)


