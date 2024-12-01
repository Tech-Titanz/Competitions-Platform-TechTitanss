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
        
        
