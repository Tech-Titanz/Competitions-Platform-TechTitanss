import os, tempfile, pytest, logging, unittest
from werkzeug.security import check_password_hash, generate_password_hash

from App.main import create_app
from App.database import db, create_db
from datetime import datetime
from App.controllers.commands import *
from App.models import User, Competition, Result
from App.controllers import (
    create_user,
    get_all_users_json,
    login,
    get_user,
    update_user,
    create_competition,   
    delete_competition,
)


LOGGER = logging.getLogger(__name__)

'''
   Unit Tests
'''
class UserUnitTests(unittest.TestCase):

    def test_new_user(self):
        user = User("bob", "bobpass")
        assert user.username == "bob"

    # pure function no side effects or integrations called
    def test_get_json(self):
        user = User("bob", "bobpass")
        user_json = user.get_json()
        self.assertDictEqual(user_json, {"id": None, "username": "bob", "is_moderator": False})

    
    def test_hashed_password(self):
        password = "mypass"
        user = User("bob", password)
        hashed = user.password
        assert user.password != password
        assert check_password_hash(user.password, password)

    def test_check_password(self):
        password = "mypass"
        user = User("bob", password)
        assert user.check_password(password)
        
        
class CompetitionUnitTests(unittest.TestCase):
    
    def setUp(self):
        Competition.query.delete()
        db.session.commit()

    def test_create_competition(self):
        """Test creating a new competition"""
       
        command = CreateCompetitionsCommand(
            "Hackattack", "Test competition", "12/12/2024", 100, 30
        )

        error, competition = command.execute()

        self.assertIsNone(error)
        self.assertEqual(competition.name, "Hackattack")
        self.assertEqual(competition.date, datetime.strptime("2024-12-12", "%Y-%m-%d").date())
        self.assertEqual(competition.description, "Test competition")
        self.assertEqual(competition.participants_amount, 100)
        self.assertEqual(competition.duration, 30)
        
        
    def test_update_competition(self):
        command_create = CreateCompetitionsCommand(
        "Hackattack", "Test competition", "2024-12-12", 100, 30  # Ensure arguments are in the right order
    )

        error, competition = command_create.execute()

    
        self.assertIsNone(error, f"Error creating competition: {error}")
        self.assertIsNotNone(competition, "Competition object is None after creation")

   
        command_update = UpdateCompetitionCommand(competition.id, "NewHackattack", "2024-12-15")
        error, updated_competition = command_update.execute()

        self.assertIsNone(error, f"Error updating competition: {error}")
        self.assertEqual(updated_competition.name, "NewHackattack")
        self.assertEqual(updated_competition.date, datetime.strptime("2024-12-15", "%Y-%m-%d").date())
        
        
    def test_delete_competition(self):
        command_create = CreateCompetitionsCommand(
            "Hackattack", "Test competition","2024-12-12", 100, 30
        )
        error, competition = command_create.execute()

  
        command_delete = DeleteCompetitionCommand(competition.id)
        error, message = command_delete.execute()

        # Assert that no error occurred
        self.assertIsNone(error)
        self.assertEqual(message, f"Competition with ID {competition.id} has been deleted.")
       
    

'''
    Integration Tests
'''

# This fixture creates an empty database for the test and deletes it after the test
# scope="class" would execute the fixture once and resued for all methods in the class
@pytest.fixture(autouse=True, scope="module")
def empty_db():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'})
    create_db()
    yield app.test_client()
    db.drop_all()


def test_authenticate():
    user = create_user("bob", "bobpass")
    assert login("bob", "bobpass") != None

class UsersIntegrationTests(unittest.TestCase):

    def test_create_user(self):
        user = create_user("rick", "bobpass")
        assert user.username == "rick"

    def test_get_all_users_json(self):
        users_json = get_all_users_json()
        self.assertListEqual(
            [
                {"id": 1, "username": "bob", "is_moderator": False},
                {"id": 2, "username": "rick", "is_moderator": False},
            ],
            users_json
        )

    # Tests data changes in the database
    def test_update_user(self):
        update_user(1, "ronnie")
        user = get_user(1)
        assert user.username == "ronnie"
        
        
class CompetitionIntegrationTests(unittest.TestCase):
    def test_create_competition(self):
        command = CreateCompetitionsCommand(
            "Hackathon 2024", "Annual coding event", "2024-12-12", 200, 8
        )
        error, competition = command.execute()

        assert error is None
        assert competition is not None
        assert competition.name == "Hackathon 2024"
        assert competition.date == datetime.strptime("2024-12-12", "%Y-%m-%d").date()
        assert competition.description == "Annual coding event"
        assert competition.participants_amount == 200
        assert competition.duration == 8

    
    
    def test_update_competition(self):
        # Create a competition to update
        create_command = CreateCompetitionsCommand(
            "Update Test", "Initial Description", "2024-12-10", 150, 4
        )
        _, competition = create_command.execute()

        # Update the competition
        update_command = UpdateCompetitionCommand(competition.id, "Updated Name", "2024-12-15")
        error, updated_competition = update_command.execute()

        assert error is None
        assert updated_competition.name == "Updated Name"
        assert updated_competition.date == datetime.strptime("2024-12-15", "%Y-%m-%d").date()


    def test_delete_competition(self):
       
        create_command = CreateCompetitionsCommand(
            "Delete Test", "To be deleted", "2024-12-20", 100, 5
        )
        _, competition = create_command.execute()

        delete_command = DeleteCompetitionCommand(competition.id)
        error, message = delete_command.execute()

        assert error is None
        assert message == f"Competition with ID {competition.id} has been deleted."
        deleted_competition = Competition.query.get(competition.id)
        assert deleted_competition is None

    def test_get_competition_details(self):
        create_command = CreateCompetitionsCommand(
            "Details Test", "Fetching details", "2024-12-25", 300, 12
        )
        _, competition = create_command.execute()

        # Fetch competition details
        details_command = GetCompetitionDetailsCommand(competition.id)
        error, fetched_competition = details_command.execute()

        assert error is None
        assert fetched_competition.id == competition.id
        assert fetched_competition.name == "Details Test"

    def test_import_competitions(self):
        # Write a temporary CSV file for importing competitions
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w") as temp_file:
            temp_file.write(
                "name,date,description,participants_amount,duration\n"
                "Import Test 1,2024-12-10,First Import,50,5\n"
                "Import Test 2,2024-12-15,Second Import,100,10\n"
            )
            temp_file_path = temp_file.name

        import_command = ImportCompetitionsCommand(temp_file_path)
        import_command.execute()

        competition1 = Competition.query.filter_by(name="Import Test 1").first()
        competition2 = Competition.query.filter_by(name="Import Test 2").first()

        assert competition1 is not None
        assert competition1.date == datetime.strptime("2024-12-10", "%Y-%m-%d").date()
        assert competition1.description == "First Import"

        assert competition2 is not None
        assert competition2.date == datetime.strptime("2024-12-15", "%Y-%m-%d").date()
        assert competition2.description == "Second Import"

        os.remove(temp_file_path)
    
    
    def test_user_join_competition_success(self):
        # Create a user and competition for testing
        create_user_command = RegisterUserCommand("john", "johnpass")
        user = create_user_command.execute()

        create_competition_command = CreateCompetitionsCommand(
            "Join Test", "Test competition for user join", "2024-12-10", 2, 4
        )
        _, competition = create_competition_command.execute()

        # User joins the competition
        join_command = JoinCompetitionCommand(user.id, competition.id)
        error, updated_competition = join_command.execute()

        assert error is None
        assert updated_competition is not None
        assert len(updated_competition.participants) == 1
        assert updated_competition.participants[0].user_id == user.id