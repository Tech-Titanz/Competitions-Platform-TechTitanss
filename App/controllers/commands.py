from abc import ABC, abstractmethod
from collections import defaultdict
from App.models import User, Competition,Result
from App.database import db
from datetime import datetime
from dateutil import parser
import csv

from App.models.competition import Participant


class Command(ABC):
    @abstractmethod
    def execute(self):
        pass
    
    
class RegisterUserCommand(Command):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        

    def execute(self):
        newuser = User(username=self.username, password=self.password)
        db.session.add(newuser)
        db.session.commit()
        return newuser
    
    
class LoginUserCommand(Command):
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def execute(self):
        user = User.query.filter_by(username=self.username).first()
        if user and user.password == self.password:
            return user
        return None


class CreateCompetitionsCommand:
    def __init__(self, name, description, date, participants_amount, duration):
        self.name = name
        self.description = description
        self.date = date
        self.participants_amount = participants_amount
        self.duration = duration

    def parse_date(self, date_str):
        try:
            return parser.parse(date_str).date()
        except ValueError:
            raise ValueError(f"Invalid date format: '{date_str}'. Expected formats: 'YYYY-MM-DD', 'MM/DD/YYYY'.")

    def execute(self):
        try:
           
            existing_competition = Competition.query.filter_by(name=self.name).first()
            if existing_competition:
                return f"Competition with name '{self.name}' already exists.", None

            parsed_date = self.parse_date(self.date)

            competition = Competition(
                name=self.name,
                description=self.description,
                date=parsed_date,
                participants_amount=self.participants_amount,
                duration=self.duration,
            )
            db.session.add(competition)
            db.session.commit()
            return None, competition
        except ValueError as e:
     
            return str(e), None
        except Exception as e:
            db.session.rollback()
            return str(e), None

    
class UpdateCompetitionCommand(Command):
    def __init__(self, competition_id, new_name, new_date):
        self.competition_id = competition_id
        self.new_name = new_name
        self.new_date = new_date

    def execute(self):
        competition = Competition.query.get(self.competition_id)
        if not competition:
            return f'Competition with ID {self.competition_id} not found!', None

        competition.name = self.new_name
        try:
            competition.date = datetime.strptime(self.new_date, "%Y-%m-%d").date()
        except ValueError:
            return f'Invalid date format: {self.new_date}. Please use YYYY-MM-DD.', None

        db.session.commit()
        return None, competition
    
    
class DeleteCompetitionCommand(Command):
    def __init__(self, competition_id):
        self.competition_id = competition_id

    def execute(self):
        competition = Competition.query.get(self.competition_id)
        if not competition:
            return f'Competition with ID {self.competition_id} not found!', None

        db.session.delete(competition)
        db.session.commit()
        return None, f'Competition with ID {self.competition_id} has been deleted.'


class GetCompetitionDetailsCommand(Command):
    def __init__(self, competition_id):
        self.competition_id = competition_id

    def execute(self):
        competition = Competition.query.get(self.competition_id)
        if not competition:
            return f"No competition found with ID '{self.competition_id}'.", None
        return None, competition


class ImportCompetitionsCommand(Command):
    def __init__(self, competition_file):
        self.competition_file = competition_file

    def execute(self):
        try:
            # Open the CSV file
            with open(self.competition_file, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Iterate over each row in the CSV
                for row in reader:
                    competition_name = row['name']
                    competition_date_str = row['date']
                    competition_description = row['description']
                    participants_amount = int(row['participants_amount'])
                    duration = int(row['duration'])
                    
                    try:
                        # Parse the date from string to datetime object
                        competition_date = datetime.strptime(competition_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        print(f"Error parsing date {competition_date_str} for competition {competition_name}")
                        continue
                    
                    # Check if the competition already exists
                    competition = Competition.query.filter_by(name=competition_name).first()
                    
                    if not competition:
                        # Create a new competition if it does not exist
                        competition = Competition(
                            name=competition_name,
                            date=competition_date,
                            description=competition_description,
                            participants_amount=participants_amount,
                            duration=duration
                        )
                        # Add and commit the competition to the database
                        db.session.add(competition)
                        db.session.commit()
                    else:
                        print(f"Competition with name '{competition_name}' already exists. Skipping...")
                        
            print("Competitions imported successfully.")
        
        except FileNotFoundError as e:
            print(f"File not found: {e.filename}")
        except Exception as e:
            print(f"An error occurred: {e}")
            

class ImportParticipantsCommand(Command):
    def __init__(self, participants_file):
        self.participants_file = participants_file

    def execute(self):
        try:
            with open(self.participants_file, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    participant_name = row['name']
                    competition_id = row['competition_id']
                    
                    competition = Competition.query.get(competition_id)
                    if not competition:
                        print(f"Competition with ID {competition_id} not found!")
                        continue
                    
                    # Create a new participant if they don't exist
                    participant = Participant.query.filter_by(name=participant_name, competition_id=competition_id).first()
                    if not participant:
                        participant = Participant(name=participant_name, competition_id=competition_id)
                        db.session.add(participant)
                        db.session.commit()
                    else:
                        print(f"Participant '{participant_name}' already exists for competition ID {competition_id}. Skipping...")
            
            print("Participants imported successfully.")
        except FileNotFoundError as e:
            print(f"File not found: {e.filename}")
        except Exception as e:
            print(f"An error occurred: {e}")

class ImportResultsCommand(Command):
    def __init__(self, results_file):
        self.results_file = results_file

    def execute(self):
        try:
            with open(self.results_file, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    participant_name = row['participant_name']
                    try:
                        score = int(row['score'])  # Make sure to convert score to integer
                    except ValueError:
                        print(f"Invalid score value: {row['score']} for participant {participant_name}")
                        continue
                    
                    competition_id = row['competition_id']
                    competition = Competition.query.get(competition_id)
                    if not competition:
                        print(f"Competition with ID {competition_id} not found!")
                        continue
                    
                    participant = Participant.query.filter_by(name=participant_name, competition_id=competition_id).first()
                    if participant:
                        result = Result(participant_id=participant.id, competition_id=competition.id, score=score)
                        db.session.add(result)
                        db.session.commit()
                    else:
                        print(f"Participant {participant_name} not found for competition ID {competition_id}.")
                        
            print("Results imported successfully.")
        except FileNotFoundError as e:
            print(f"File not found: {e.filename}")
        except Exception as e:
            print(f"An error occurred: {e}")

            
class AddCompetitionResultsCommand(Command):
    def __init__(self, competition_id, results):
        self.competition_id = competition_id
        self.results = results

    def execute(self):
        competition = Competition.query.get(self.competition_id)
        if competition:
            # Assuming self.results is a list of Result objects
            for result in self.results:
                db.session.add(result)
            db.session.commit()
            print(f"Results added for competition {competition.name}.")
            return competition
        else:
            print(f"Competition with ID {self.competition_id} not found.")
            return None


class JoinCompetitionCommand:
    def __init__(self, user_id, competition_id):
        self.user_id = user_id
        self.competition_id = competition_id

    def execute(self):
       
        competition = Competition.query.get(self.competition_id)
        user = User.query.get(self.user_id)

      
        if not competition:
            return "Competition not found.", None
        if not user:
            return "User not found.", None

    
        if len(competition.participants) >= competition.participants_amount:
            return "Competition is full.", None

      
        existing_participant = Participant.query.filter_by(user_id=user.id, competition_id=competition.id).first()
        if existing_participant:
            return "User already joined this competition.", None

        
        new_participant = Participant(name=user.username, user_id=user.id, competition_id=competition.id)
        db.session.add(new_participant)
        db.session.commit()

        return None, competition

class ViewProfileCommand(Command):
    def __init__(self, user_id):
        self.user_id = user_id

    def execute(self):
        user = User.query.get(self.user_id)
        if not user:
            return f"User with ID {self.user_id} not found.", None
        
        
        results = Result.query.join(Participant).filter(Participant.user_id == self.user_id).all()

        profile_details = {
            "username": user.username,
            "rank": user.rank,
            "competitions": []
        }

        for result in results:
            competition = Competition.query.get(result.competition_id)
            profile_details["competitions"].append({
                "competition_name": competition.name,
                "score": result.score,
                "date": competition.date
            })

        return profile_details


class ViewLeaderboardCommand(Command):
    def __init__(self, competition_id=None):
        self.competition_id = competition_id  
    def execute(self):
        if self.competition_id:
           
            results = Result.query.filter_by(competition_id=self.competition_id).join(User).all()
            leaderboard = sorted(results, key=lambda x: x.score, reverse=True)
        else:
      
            results = Result.query.join(User).all()
            user_scores = defaultdict(int)

            for result in results:
                user_scores[result.user.id] += result.score

            leaderboard = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)

  
        leaderboard_data = []
        for entry in leaderboard:
            if isinstance(entry, tuple):  
                user = User.query.get(entry[0])
                leaderboard_data.append((user.username, entry[1]))
            else:  
                leaderboard_data.append((entry.user.username, entry.score))

        return leaderboard_data

    
class UpdateParticipantCommand(Command):
    def __init__(self, participant_id, new_name, new_competition_id):
        self.participant_id = participant_id
        self.new_name = new_name
        self.new_competition_id = new_competition_id

    def execute(self):
        participant = Participant.query.get(self.participant_id)
        if not participant:
            return f"Participant with ID {self.participant_id} not found!", None

        participant.name = self.new_name
        competition = Competition.query.get(self.new_competition_id)
        if competition:
            participant.competition_id = self.new_competition_id
        else:
            return f"Competition with ID {self.new_competition_id} not found!", None
        
        db.session.commit()
        return None, participant
    
class ViewCompetitionParticipantsCommand(Command):
    def __init__(self, competition_id):
        self.competition_id = competition_id

    def execute(self):
        competition = Competition.query.get(self.competition_id)
        if not competition:
            return f"Competition with ID {self.competition_id} not found!", None
        
        participants = Participant.query.filter_by(competition_id=self.competition_id).all()
        return None, participants
    
    
    
#found defaultdict from research and assistance from chatgpt
class AggregateProfileCommand(Command):
    def __init__(self, competition_id=None):
        self.competition_id = competition_id

    def execute(self):
        participant_scores = defaultdict(int)
        participant_competitions = defaultdict(set)

        if self.competition_id:
            results = Result.query.filter_by(competition_id=self.competition_id).all()
        else:
            results = Result.query.all()

        for result in results:
            participant_scores[result.participant.name] += result.score
            participant_competitions[result.participant.name].add(result.competition.name)

        sorted_participants = sorted(participant_scores.items(), key=lambda x: x[1], reverse=True)

        rankings = []
        rank = 1
        for participant_name, total_score in sorted_participants:
            competitions_participated = len(participant_competitions[participant_name])
            rankings.append((participant_name, total_score, competitions_participated))
            rank += 1

        return rankings


                
                
                