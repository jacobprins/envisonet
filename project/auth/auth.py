from flask import Blueprint, render_template, redirect, url_for, request, flash, session, app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from .models import User
from .. import db

auth = Blueprint('auth', __name__)

# Route that serves the login page
@auth.route('/login')
def login():
    return render_template('/auth/login.html')

# Route that handles post requests from the login page
@auth.route('/login', methods=['POST'])
def login_post():
    # Gets login information from the post request
    username = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    user = User.query.filter_by(username=username).first()

    # Checks if the user actually exists and takes the password, hashes it, and compares it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('Please check your login credentials and try again.')
        # Reloads the page if the user doesn't exist or password is wrong
        return redirect(url_for('auth.login'))

    # If the above check passes, the user has the right credentials, so log them in
    login_user(user, remember=remember)

    # After login, redirect to service page
    return redirect(url_for('main.service'))

# Route that serves the registration page
@auth.route('/register')
def register():
    return render_template('/auth/register.html')

# Route that handles post requests from the registration page
@auth.route('/register', methods=['POST'])
def register_post():
    # Gets registration information from the post request
    username = request.form.get('username')
    password = request.form.get('password')

    # If this returns a user, then the username already exists in database
    user = User.query.filter_by(username=username).first()

    # If a username that is not already used and a password are submitted, add the user to the database
    if username != '' and password != '' and not user: 
        # Creates a new user with the form data and hashes the password so the plaintext version isn't saved.
        new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))

        # Add the new user to the database
        db.session.add(new_user)
        db.session.commit()

        # Redirects the user to the login page
        return redirect(url_for('auth.login'))
    
    # Error handling for edge-cases that provides user feedback
    elif user:
        flash('Username is taken, try again')
        return redirect(url_for('auth.register'))
    elif username == '' and password == '':
        flash('You must input a username and a password.')
        return redirect(url_for('auth.register'))
    elif username == "":
        flash('You must input a username.')
        return redirect(url_for('auth.register'))
    elif password == "":
        flash('You must input a password.')
        return redirect(url_for('auth.register'))
    else:
        flash('There was an error')
        return redirect(url_for('auth.register'))

# Route to log the user out and redirects to the login page
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))