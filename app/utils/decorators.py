from functools import wraps
from flask import session, flash, redirect, url_for, request, abort
from app.models import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        user = User.query.get(user_id)
        if not user or not user.is_active:
            session.clear()
            flash('Your account has been deactivated or does not exist.', 'danger')
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Please log in with admin privileges.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        user = User.query.get(user_id)
        if not user or not user.is_active or not user.is_admin:
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('games.index'))
            
        return f(*args, **kwargs)
    return decorated_function


def anonymous_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_id'):
            return redirect(url_for('games.index'))
        return f(*args, **kwargs)
    return decorated_function

