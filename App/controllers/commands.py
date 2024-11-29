from abc import ABC, abstractmethod
from App.models import User, Competition,Result
from App.database import db
from datetime import datetime
from dateutil import parser
import csv


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
        """ Try parsing the date with multiple formats or with dateutil parser """
        try:
            # Try using dateutil's parser for flexible date handling
            return parser.parse(date_str).date()
        except ValueError:
            raise ValueError(f"Invalid date format: '{date_str}'. Expected formats: 'YYYY-MM-DD', 'MM/DD/YYYY'.")

    def execute(self):
        try:
            # Check if a competition with the same name already exists
            existing_competition = Competition.query.filter_by(name=self.name).first()
            if existing_competition:
                return f"Competition with name '{self.name}' already exists.", None

            # Parse the date using the flexible date parser
            parsed_date = self.parse_date(self.date)

            # Create a new competition
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
            # Handle value errors specifically for date parsing
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

class ImportResultsCommand(Command):
    def __init__(self, results_file):
        self.results_file = results_file

    def execute(self):
        try:
            with open(self.results_file, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    participant_name = row['participant_name']
                    score = row['score']
                    competition_id = row['competition_id']
                    
                    competition = Competition.query.get(competition_id)
                    if not competition:
                        print(f"Competition with ID {competition_id} not found!")
                        continue
                    
                    participant = User.query.filter_by(username=participant_name).first()
                    if participant:
                        result = Result(user_id=participant.id, competition_id=competition.id, score=score)
                        db.session.add(result)
                        db.session.commit()
                        
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
            competition.results = self.results
            db.session.commit()
            return competition
        return None


class ViewProfileCommand(Command):
    def __init__(self, user_id):
        self.user_id = user_id

    def execute(self):
        return User.query.get(self.user_id)


class ViewLeaderboardCommand(Command):
    def __init__(self):
        pass

    def execute(self):
        return User.query.order_by(User.rank.desc()).all()
    


                
                
                