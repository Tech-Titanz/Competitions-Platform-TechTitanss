from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, current_user as jwt_current_user
from App.controllers import (
    get_competition, update_competition, delete_competition, 
    create_competition, import_competitions, import_results, get_results
)
from App.models import Competition, Result, CompetitionController
from App.database import db
from datetime import datetime
from App.controllers.commands import *
from App.models.user import User, UserController

competition_views = Blueprint('competition_views', __name__, template_folder='../templates')

### ROUTES ###

@competition_views.route('/api/competitions', methods=['GET'])
def get_competitions():
    # Regular users and moderators can view the competitions
    competitions = Competition.query.all()
    return jsonify([
        {
            'id': competition.id,
            'name': competition.name,
            'date': competition.date.isoformat(),
            'description': competition.description
        }
        for competition in competitions
    ]), 200
    

@competition_views.route('/api/competitions/<int:competition_id>', methods=['GET'])
def get_competition_details(competition_id):
    # Regular users and moderators can view the competition details
    competition = Competition.query.get_or_404(competition_id)
    return jsonify({
        'id': competition.id,
        'name': competition.name,
        'date': competition.date.isoformat(),
        'description': competition.description
    }), 200

@competition_views.route('/api/competitions/<int:competition_id>/participants', methods=['GET'])
def get_competition_participants(competition_id):
    # Regular users and moderators can view the participants of a competition
    competition = Competition.query.get_or_404(competition_id)
    participants = competition.participants  # Assuming participants are a related model or list

    return jsonify([
        {
            'id': participant.id,
            'username': participant.username,
            'team': participant.team  # Assuming the participant has a 'team' attribute
        }
        for participant in participants
    ]), 200

@competition_views.route('/api/competitions', methods=['POST'])
@jwt_required()
def create_competition_endpoint():
    # Only moderators can create competitions
    if not jwt_current_user() or not jwt_current_user().is_moderator:
        return jsonify({'message': 'Permission denied'}), 403

    data = request.json
    required_fields = ['name', 'description', 'date', 'participants_amount', 'duration']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields.'}), 400

    try:
        command = CreateCompetitionsCommand(
            data['name'], data['description'], 
            data['date'], data['participants_amount'], data['duration']
        )
        controller = CompetitionController(command)
        error, competition = controller.execute()

        if error:
            return jsonify({"message": error}), 400

        return jsonify({
            "message": "Competition created successfully!",
            "competition": competition.get_json()
        }), 201

    except Exception as e:
        return jsonify({'message': f"Error: {str(e)}"}), 500

@competition_views.route('/api/competitions/<int:competition_id>', methods=['PUT'])
@jwt_required()
def update_competition_endpoint(competition_id):
    # Only moderators can update competitions
    if not jwt_current_user() or not jwt_current_user().is_moderator:
        return jsonify({'message': 'Permission denied'}), 403

    competition = Competition.query.get_or_404(competition_id)
    data = request.json

    if 'name' in data:
        competition.name = data['name']
    if 'description' in data:
        competition.description = data['description']
    if 'date' in data:
        try:
            competition.date = datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400
    if 'participants_amount' in data:
        competition.participants_amount = data['participants_amount']
    if 'duration' in data:
        competition.duration = data['duration']

    db.session.commit()
    return jsonify({'message': 'Competition updated successfully!'}), 200

@competition_views.route('/api/competitions/<int:competition_id>', methods=['DELETE'])
@jwt_required()
def delete_competition_endpoint(competition_id):
    # Only moderators can delete competitions
    if not jwt_current_user() or not jwt_current_user().is_moderator:
        return jsonify({'message': 'Permission denied'}), 403

    competition = Competition.query.get_or_404(competition_id)
    db.session.delete(competition)
    db.session.commit()
    return jsonify({'message': 'Competition deleted successfully.'}), 200

@competition_views.route('/api/competitions/import', methods=['POST'])
@jwt_required()
def import_competitions_endpoint():
    # Only moderators can import competitions
    if not jwt_current_user() or not jwt_current_user().is_moderator:
        return jsonify({'message': 'Permission denied'}), 403

    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'message': 'No file provided.'}), 400

    try:
        
        count = import_competitions(file)
        return jsonify({'message': f'{count} competitions imported successfully.'}), 200
    except Exception as e:
        return jsonify({'message': f"Error importing competitions: {str(e)}"}), 500

@competition_views.route('/api/results', methods=['POST'])
@jwt_required()
def upload_results_endpoint():

    if not jwt_current_user() or not jwt_current_user().is_moderator:
        return jsonify({'message': 'Permission denied'}), 403

    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({'message': 'No file provided.'}), 400

    try:
       
        count = import_results(file)
        return jsonify({'message': f'{count} results uploaded successfully.'}), 200
    except Exception as e:
        return jsonify({'message': f"Error uploading results: {str(e)}"}), 500

@competition_views.route('/api/leaderboard', methods=['GET'])
def leaderboard_endpoint():
    results = Result.query.order_by(Result.score.desc()).all()
    leaderboard = [
        {
            'username': User.query.get(result.user_id).username,
            'competition': Competition.query.get(result.competition_id).name,
            'score': result.score
        }
        for result in results
    ]
    return jsonify({'leaderboard': leaderboard}), 200

@competition_views.route('/api/competitions/join', methods=['POST'])
def join_competition():
    # Get the data from the request
    data = request.get_json()
    username = data.get('username')
    competition_id = data.get('competition_id')

    # Fetch the user and competition from the database
    user = User.query.filter_by(username=username).first()
    competition = Competition.query.get(competition_id)

    if not user:
        return jsonify({"error": f"User '{username}' not found."}), 404
    if not competition:
        return jsonify({"error": f"Competition with ID {competition_id} not found."}), 404

    # Check if the competition is full
    if len(competition.participants) >= competition.participants_amount:
        return jsonify({"error": "Competition is full."}), 400

    # Check if the user has already joined the competition
    existing_participant = Participant.query.filter_by(user_id=user.id, competition_id=competition.id).first()
    if existing_participant:
        return jsonify({"error": "User already joined this competition."}), 400

    # Create a new participant
    new_participant = Participant(name=user.username, user_id=user.id, competition_id=competition.id)
    db.session.add(new_participant)
    db.session.commit()

    return jsonify({
        "message": f"User {user.username} successfully joined the competition '{competition.name}'!"
    }), 200
