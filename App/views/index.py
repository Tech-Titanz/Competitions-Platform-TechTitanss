from flask import Blueprint, redirect, render_template, request, send_from_directory, jsonify, session
from App.controllers import create_user, initialize
from App.models import User
from App.models import Competition

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

    username = session['user']
    user = User.query.filter_by(username=username).first()

    return render_template('view_profile(m).html', user=user)


@index_views.route('/create_competition')
def creating_competition():
    return render_template('create_competition.html')

@index_views.route('/import_results')
def results():
    return render_template('import_results.html')


