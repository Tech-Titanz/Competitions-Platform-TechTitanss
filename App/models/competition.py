from App.database import db  
from datetime import datetime

class Competition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255))
    participants_amount = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    
    participants = db.relationship('Participant', backref='competition', lazy=True)
    results = db.relationship('Result', backref='competition', lazy=True)
    
    def __init__(self, name, description, date, participants_amount, duration):
        self.name = name
        self.description = description
        self.date = date
        self.participants_amount = participants_amount
        self.duration = duration
        
    def get_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "date": self.date.strftime("%Y-%m-%d"),
            "participants_amount": self.participants_amount,
            "duration": self.duration
        }


class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'), nullable=False)
    

    results = db.relationship('Result', backref='participant', lazy=True)
    
    def __repr__(self):
        return f"Participant('{self.name}')"


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'), nullable=False)

    def __repr__(self):
        return f"<Result {self.participant.name if self.participant else 'Unknown'} - {self.score}>"

    
class CompetitionController:
    def __init__(self, command):
        self.command = command

    def execute(self):
        return self.command.execute()
    
    