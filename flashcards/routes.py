from flashcards import app, login_manager, db
from flashcards.models import User, Score, Flashcard
from flask import request, render_template, redirect, flash, url_for
from flask_login import current_user, login_user, logout_user, login_required
import random
from werkzeug.security import check_password_hash
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if len(username) == 0 or len(password) == 0:
            flash('Username and password cannot be blank!')
            return render_template('signup.html')
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
        flash('Login successful!', 'success')
        return redirect(url_for('my_profile', user=current_user))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is not None and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('my_profile', user=current_user))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Successfully logged-out!', 'success')
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
    flash('Removed flashcard!', 'success')
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
    return render_template('quiz.html', u_id=u_id, questions=questions, correct_answers=correct_answers)


@app.route('/')
def home():  # put application's code here
    return render_template('base.html')
