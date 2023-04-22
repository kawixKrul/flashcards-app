from werkzeug.security import generate_password_hash
from datetime import datetime
from flashcards import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    flashcards = db.relationship('Flashcard', backref='user', lazy=True)
    scores = db.relationship('Score', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)


class Flashcard(db.Model):
    __tablename__ = 'flashcards'

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, question, answer, user_id):
        self.question = question
        self.answer = answer
        self.user_id = user_id


class Score(db.Model):
    __tablename__ = 'scores'

    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    scored_at = db.Column(db.DateTime, nullable=False)
    belongs = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, score, user_id, belongs):
        self.score = score
        self.scored_at = datetime.utcnow()
        self.belongs = belongs
        self.user_id = user_id
