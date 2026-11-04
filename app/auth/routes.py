import re
from urllib.parse import urlsplit
from flask import render_template, redirect, url_for, flash, request, session
from app.auth import auth_bp
from app.extensions import db
from app.models import User
from app.utils.decorators import anonymous_required, login_required
from app.utils.helpers import log_activity

def is_safe_url(target):
    if not target:
        return False
    ref_url = urlsplit(request.host_url)
    test_url = urlsplit(target)
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@auth_bp.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        errors = []
        
        # Username validation
        if not username or len(username) < 3 or len(username) > 30:
            errors.append("Username must be between 3 and 30 characters.")
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append("Username can only contain alphanumeric characters and underscores.")
        elif User.query.filter_by(username=username).first():
            errors.append("This username is already taken. Please choose another.")
            
        # Email validation
        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not email or not re.match(email_regex, email):
            errors.append("Please provide a valid email address.")
        elif User.query.filter_by(email=email).first():
            errors.append("An account with this email address already exists.")
            
        # Password validation
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")
            
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html', username=username, email=email)
            
        # Create user
        user = User(
            username=username,
            email=email,
            role='user',
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        log_activity(user.id, 'registered', None, f"Welcome to GameShelf, {user.username}!")
        
        # Log the user in directly
        session.permanent = True
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        flash(f'Welcome to GameShelf, {user.username}! Your account has been created.', 'success')
        return redirect(url_for('games.index'))
        
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))
        
        if not login_input or not password:
            flash('Please enter both your username/email and password.', 'warning')
            return render_template('auth/login.html', login_input=login_input)
            
        # Allow login by username or email
        user = User.query.filter(
            (User.username.ilike(login_input)) | (User.email.ilike(login_input))
        ).first()
        
        if not user or not user.check_password(password):
            flash('Invalid username/email or password.', 'danger')
            return render_template('auth/login.html', login_input=login_input)
            
        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return render_template('auth/login.html', login_input=login_input)
            
        # Establish session
        session.permanent = remember
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        flash(f'Welcome back, {user.username}!', 'success')
        
        next_page = request.args.get('next')
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
            
        if user.is_admin:
            return redirect(url_for('admin.overview'))
        return redirect(url_for('games.index'))
        
    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('games.index'))

