from flask import Blueprint, render_template, jsonify, request, flash, send_from_directory, redirect, url_for
from flask_jwt_extended import jwt_required, current_user, unset_jwt_cookies, set_access_cookies
from flask import session

from App.controllers import (
    login,
    get_all_users,
    register_user  # Add the function to register a new user
)

auth_views = Blueprint('auth_views', __name__, template_folder='../templates')

'''
Page/Action Routes
'''

# Route to display all users
@auth_views.route('/users', methods=['GET'])
def get_user_page():
    users = get_all_users()
    return render_template('users.html', users=users)

# Route for user identification (protected)
@auth_views.route('/identify', methods=['GET'])
@jwt_required()
def identify_page():
    return render_template('message.html', title="Identify", message=f"You are logged in as {current_user.id} - {current_user.username}")

# Login action (handles POST request)
@auth_views.route('/login', methods=['POST'])
def login_action():
    data = request.form
    token = login(data['username'], data['password'])
    response = redirect(request.referrer)

    if not token:
        flash('Bad username or password given','error')
        return response

    session['user'] = data['username']
    session['user_type'] = 'user'

    flash('Login Successful', 'success')
    reply = redirect(url_for('index_views.index_page'))
    set_access_cookies(response, token) 

    return response

# Logout action (clears session and redirects to home)
@auth_views.route('/logout', methods=['GET'])
def logout_action():
    session.pop('user', None)
    session.pop('user_type', None)

    flash("You have been logged out",'success')

    return redirect(url_for('index_views.index_page'))


@auth_views.route('/signup', methods=['POST'])
def signup_action():
    data = request.form
    username = data['username']
    password = data['password']

    # Register the user using the register_user function
    user, error = register_user(username, password)

    if error:
        flash(error, 'error')  # Show error if username already exists
        return redirect(url_for('index_views.index_page'))  # Redirect to home page or signup page

    flash('Account created successfully! Please log in.', 'success')
    return redirect(url_for('index_views.index_page'))  # Redirect to home page or login page

'''
API Routes
'''

# API login route
@auth_views.route('/api/login', methods=['POST'])
def user_login_api():
    data = request.json
    token = login(data['username'], data['password'])
    if not token:
        return jsonify(message='bad username or password given'), 401
    response = jsonify(access_token=token)
    set_access_cookies(response, token)
    return response

# API route for identifying the user (protected)
@auth_views.route('/api/identify', methods=['GET'])
@jwt_required()
def identify_user():
    return jsonify({'message': f"username: {current_user.username}, id : {current_user.id}"})

# API logout route
@auth_views.route('/api/logout', methods=['GET'])
def logout_api():
    response = jsonify(message="Logged Out!")
    unset_jwt_cookies(response)
    return response
