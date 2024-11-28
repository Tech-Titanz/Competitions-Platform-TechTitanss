import os, tempfile, pytest, logging, unittest
from werkzeug.security import check_password_hash, generate_password_hash

from App.main import create_app
from App.database import db, create_db
from datetime import datetime
from App.controllers.commands import CreateCompetitionsCommand
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

    def test_create_competition(self):
        """Test creating a new competition"""
        # Create the command to create the competition with different date formats
        command = CreateCompetitionsCommand(
            "Hackattack", "Test competition", "12/12/2024", 100, 30
        )

        # Execute the command (this will create the competition in the DB)
        error, competition = command.execute()

        # Assert that no error occurred
        self.assertIsNone(error)

        # Assert that the competition was created correctly
        self.assertEqual(competition.name, "Hackattack")
        self.assertEqual(competition.date, datetime.strptime("2024-12-12", "%Y-%m-%d").date())
        self.assertEqual(competition.description, "Test competition")
        self.assertEqual(competition.participants_amount, 100)
        self.assertEqual(competition.duration, 30)

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
        self.assertListEqual([{"id":1, "username":"bob"}, {"id":2, "username":"rick"}], users_json)

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
            "This is a test competition", 
            100, 
            30
        )

    # Assert that the competition was created and saved to the database
        assert competition is not None
        assert competition.name == "Hackattack"
        assert competition.date == datetime.strptime("2024-12-12", "%Y-%m-%d").date()
        assert competition.description == "This is a test competition"
        assert competition.participants_amount == 100
        assert competition.duration == 30

    
    
    def test_update_competition(self):
    # Create a new competition
        competition = create_competition(
            "Hackattack", 
            "2024-12-12", 
            "This is a test competition", 
            100, 
            30
        )

    # Update competition details
        competition.name = "Hackattack Updated"
        competition.date = datetime.strptime("2025-01-01", "%Y-%m-%d").date()
        competition.description = "Updated test competition"
        competition.participants_amount = 200
        competition.duration = 40
        db.session.commit()

    # Reload from DB to check if updates are saved
        updated_competition = Competition.query.get(competition.id)

    # Assert the updated values
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



        
    def test_get_results(self):
    # Create a competition
        competition = create_competition(
            "Hackattack", 
            "2024-12-12", 
            "This is a test competition", 
            100, 
            30
        )

        # Simulate getting competition results
        results = get_results(competition.id)

    # Assert that results are returned (modify this part based on your implementation of get_results)
        assert results is not None
        assert isinstance(results, list)  # Assuming results are returned as a list
        assert len(results) >= 0  # Modify the length check based on your test data



        
    def test_import_competitions():
 
        import_competitions("path/to/competitions_file.json")

        competitions = Competition.query.all()
  
        assert len(competitions) > 0
    
        competition_names = [comp.name for comp in competitions]
        assert "Hackattack" in competition_names
        assert "AnotherCompetition" in competition_names


    


