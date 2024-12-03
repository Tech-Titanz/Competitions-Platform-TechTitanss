from App.models import User
from App.database import db

def create_user(username, password):
    newuser = User(username=username, password=password)
    db.session.add(newuser)
    db.session.commit()
    return newuser

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

def get_user(id):
    return User.query.get(id)

def get_all_users(moderator=None):
    if moderator is None:
        return User.query.all() 
    return User.query.filter_by(is_moderator=moderator).all()

def get_all_users_json(moderator=None):
    users = User.query.all()
    if not users:
        return []
    return [user.get_json() for user in users]
    

def update_user(id, username):
    user = get_user(id)
    if user:
        user.username = username
        db.session.add(user)
        return db.session.commit()
    return None

def register_user(username, password, is_moderator=False):
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return None, "Username already taken"
    
    new_user = User(username=username, password=password, is_moderator=is_moderator)
    db.session.add(new_user)
    db.session.commit()
    return new_user, None


def get_user_profile(user_id):
    user = User.query.get(user_id)
    if not user:
        return None, "User not found"
    return user, None
        
    