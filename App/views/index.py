from flask import Blueprint, redirect, render_template, request, send_from_directory, jsonify
from App.controllers import create_user, initialize

index_views = Blueprint('index_views', __name__, template_folder='../templates')

@index_views.route('/', methods=['GET'])
def index_page():
    return render_template('index.html')

@index_views.route('/init', methods=['GET'])
def init():
    initialize()
    return jsonify(message='db initialized!')

@index_views.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status':'healthy'})

@index_views.route('/leaderboard')
def leaderboard():
    print("Leaderboard route accessed!")
    return render_template('leaderboard.html')

@index_views.route('/competition_list')
def list():
    return render_template('competition_list.html')

@index_views.route('/profile')
def profile():
    return render_template('view_profile.html')


