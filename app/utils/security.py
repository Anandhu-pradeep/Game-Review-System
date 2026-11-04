import secrets
from flask import session, request, abort, current_app

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

def validate_csrf():
    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
        # Exclude testing if needed or check token from form or header
        token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
        expected_token = session.get('_csrf_token')
        
        if not expected_token or not token or token != expected_token:
            abort(400, description="Invalid or missing CSRF token.")

