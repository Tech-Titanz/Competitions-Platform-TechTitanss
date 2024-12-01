import os, tempfile, pytest, logging, unittest
from werkzeug.security import check_password_hash, generate_password_hash

from App.main import create_app
from App.database import db, create_db
from datetime import datetime
from App.controllers.commands import CreateCompetitionsCommand,UpdateCompetitionCommand,DeleteCompetitionCommand
from App.models import User, Competition, Result
from App.controllers import (
    create_user,
    get_all_users_json,
    login,
    get_user,
    update_user,
    create_competition,   
    get_results,
    import_competitions,
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
    # Create a new competition
        competition = create_competition(
            "Hackattack",
            "2024-12-12",
            "Test competition",  # Update this to match the function's behavior
            100,
            30
        )

    # Assert that the competition was created and saved to the database
        assert competition is not None
        assert competition.name == "Hackattack"
        assert competition.date == datetime.strptime("2024-12-12", "%Y-%m-%d").date()
        assert competition.description == "Test competition"  # Ensure this matches the input

    
    
    def test_update_competition(self):
    # Create a new competition
        competition = create_competition(
            "Hackattack", 
            "2024-12-12", 
            "This is a test competition", 
            100, 
            30
        )

        competition.name = "Hackattack Updated"
        competition.date = datetime.strptime("2025-01-01", "%Y-%m-%d").date()
        competition.description = "Updated test competition"
        competition.participants_amount = 200
        competition.duration = 40
        db.session.commit()

        updated_competition = Competition.query.get(competition.id)

        assert updated_competition.name == "Hackattack Updated"
        assert updated_competition.date == datetime.strptime("2025-01-01", "%Y-%m-%d").date()
        assert updated_competition.description == "Updated test competition"
        assert updated_competition.participants_amount == 200
        assert updated_competition.duration == 40



    def test_delete_competition(self):
        competition = create_competition(
            "Hackattack", 
            "2024-12-12",  # Correct placement of date
            "This is a test competition",  # Correct placement of description
            100, 
            30
    )
        delete_competition(competition.id)
        deleted_competition = Competition.query.get(competition.id)
        assert deleted_competition is None

    # def test_get_results(self):
    # # Create a competition
    #     competition = create_competition(
    #         "Hackattack",
    #         "2024-12-12",
    #         "This is a test competition",
    #         100,
    #         30
    #     )

    # # Simulate getting competition results
    #     results = get_results(competition.id)

    # # Assert that results are returned as a list (even if empty)
    #     assert results is not None
    #     assert isinstance(results, list)  # Ensure it is a list
    #     assert len(results) == 0  # Expecting no results since none are added

    
    # def test_import_competitions():

    #     competition_file_path = competitions.csv
    

    #     import_competitions(competition_file_path)
    
 
    #     competitions = Competition.query.all()


    #     assert len(competitions) > 0, "No competitions found in the database after import"
    
   
    #     competition_names = [comp.name for comp in competitions]

    
    #     assert "Hackattack" in competition_names, "'Hackattack' not found in imported competitions"
    #     assert "Python Mastery" in competition_names, "'Python Mastery' not found in imported competitions"
    #     assert "AI Innovation Sprint" in competition_names, "'AI Innovation Sprint' not found in imported competitions"
    #     assert "AnotherCompetition" not in competition_names, "'AnotherCompetition' should not be in the list"

    #     print("Competitions import test passed successfully!")