import os
from pathlib import Path
from flask import Flask, session, request, abort, render_template
from config import config
from app.extensions import db, migrate
from app.utils.security import generate_csrf_token, validate_csrf

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))

    # Ensure upload directories exist
    for folder in [
        app.config['UPLOAD_FOLDER'],
        app.config['COVERS_FOLDER'],
        app.config['BANNERS_FOLDER'],
        app.config['AVATARS_FOLDER']
    ]:
        Path(folder).mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.auth import auth_bp
    from app.games import games_bp
    from app.reviews import reviews_bp
    from app.users import users_bp
    from app.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(games_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(admin_bp)

    # Global CSRF validation on mutating methods
    @app.before_request
    def csrf_protect():
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Allow skipping only if explicitly marked (none currently)
            token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
            expected_token = session.get('_csrf_token')
            if not expected_token or not token or token != expected_token:
                abort(400, description="Invalid or missing CSRF token.")

    # Context processors
    @app.context_processor
    def inject_globals():
        from app.models import User, Notification
        current_user = None
        unread_count = 0
        if 'user_id' in session:
            current_user = User.query.get(session['user_id'])
            if current_user and not current_user.is_active:
                session.clear()
                current_user = None
            elif current_user:
                unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

        online_users = User.query.filter_by(is_active=True).order_by(User.id.asc()).limit(4).all()

        return {
            'csrf_token': generate_csrf_token,
            'current_user': current_user,
            'unread_notifications_count': unread_count,
            'online_users': online_users
        }

    # Jinja custom filters
    @app.template_filter('format_date')
    def format_date(value, format='%b %d, %Y'):
        if value is None:
            return ''
        return value.strftime(format)

    @app.template_filter('time_ago')
    def time_ago(dt):
        from datetime import datetime, timezone
        if not dt:
            return ''
        now = datetime.utcnow()
        diff = now - dt
        seconds = diff.total_seconds()
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours}h ago"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days}d ago"
        else:
            return dt.strftime('%b %d, %Y')

    # Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html', error=e), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html', error=e), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html', error=e), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html', error=e), 500

    return app

