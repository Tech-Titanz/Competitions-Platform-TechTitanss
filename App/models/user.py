from werkzeug.security import check_password_hash, generate_password_hash
from App.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username =  db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    is_moderator = db.Column(db.Boolean, default=False)
    

    def __init__(self, username, password, is_moderator =False):
        self.username = username
        self.set_password(password)
        self.is_moderator = is_moderator

    def get_json(self):
        return{
            'id': self.id,
            'username': self.username,
            'is_moderator': self.is_moderator
        }

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)
    

class UserController:
    def __init__(self, command):
        self.command = command

    def execute(self):
        return self.command.execute()


class ModeratorController:
    def __init__(self, command):
        self.command = command

    def execute(self):
        return self.command.execute()
    

  

