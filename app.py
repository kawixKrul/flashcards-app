from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir + '/instance', 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user is None:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            flash('You have successfully signed up!', 'success')
            login_user(user)
            return redirect(url_for('my_profile', user=current_user))
        else:
            flash('That username is already taken.', 'error')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('my_profile', user=current_user))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is not None and check_password_hash(user.password_hash, password):
            login_user(user)
            print('login succesful')
            return redirect(url_for('my_profile', user=current_user))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/my-profile', methods=['GET', 'POST'])
@login_required
def my_profile():
    if request.method == 'POST':
        question = request.form['question']
        answer = request.form['answer']
        card = Flashcard(answer=answer, question=question, user_id=current_user.id)
        db.session.add(card)
        db.session.commit()
        flash('Successfully added a new flashcard!', 'success')

    flashcards = Flashcard.query.filter_by(user_id=current_user.id).all()
    my_scores = Score.query.filter_by(belongs=current_user.username).all()
    return render_template('my_profile.html', user=current_user, flashcards=flashcards, my_scores=my_scores)


@app.route('/my-profile/remove/<int:fs_id>', methods=['POST'])
@login_required
def remove(fs_id):
    fs = Flashcard.query.filter_by(id=fs_id).first()
    db.session.delete(fs)
    db.session.commit()
    return redirect(url_for('my_profile'))


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    user_list = User.query.filter(User.id != current_user.id).all()
    return render_template('users.html', users=user_list, user=current_user)


@app.route('/users/<int:u_id>', methods=['GET', 'POST'])
@login_required
def user_profile(u_id):
    flashcards = Flashcard.query.filter_by(user_id=u_id).all()
    scores = Score.query.filter_by(user_id=u_id).all()
    return render_template('user_profile.html', flashcards=flashcards, u_id=u_id, user=current_user, scores=scores)


@app.route('/quiz/<int:u_id>', methods=['GET', 'POST'])
@login_required
def quiz(u_id):
    if request.method == 'POST':
        score = request.json['score']
        current_score = Score.query.filter(Score.user_id == u_id, Score.belongs == current_user.username).first()
        if current_score is not None and current_score.score < score:
            current_score.score = score
            current_score.time = datetime.utcnow()
            flash('Score updated! New best!', 'success')
        elif current_score is not None and current_score.score > score:
            flash('Not your best attempt. Try harder!', 'success')
        elif current_score is None:
            new_score = Score(score=score, user_id=u_id, belongs=current_user.username)
            db.session.add(new_score)
            flash('New score added!', 'success')
        db.session.commit()
        return redirect(url_for('user_profile', u_id=u_id))

    sample = random.sample(Flashcard.query.filter_by(user_id=u_id).all(), 10)
    questions = [s.question for s in sample]
    correct_answers = [s.answer for s in sample]
    for i in zip(questions, correct_answers):
        print(i)
    return render_template('quiz.html', u_id=u_id, questions=questions, correct_answers=correct_answers)


@app.route('/')
def home():  # put application's code here
    return render_template('base.html')


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
