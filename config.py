import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'gameshelf-dev-default-secret-key-2026')
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        pg_user = os.environ.get('POSTGRES_USER', 'gameshelf_user')
        pg_pass = os.environ.get('POSTGRES_PASSWORD', 'gameshelf_secure_password_2026')
        pg_host = os.environ.get('POSTGRES_HOST', 'localhost')
        pg_port = os.environ.get('POSTGRES_PORT', '5432')
        pg_db = os.environ.get('POSTGRES_DB', 'gameshelf_db')
        database_url = f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
        
    # Heroku / SQLAlchemy compatibility for postgres:// or postgresql:// without driver
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    BASE_DIR = basedir
    STATIC_FOLDER = basedir / 'app' / 'static'
    UPLOAD_FOLDER = STATIC_FOLDER / 'uploads'
    COVERS_FOLDER = UPLOAD_FOLDER / 'covers'
    BANNERS_FOLDER = UPLOAD_FOLDER / 'banners'
    AVATARS_FOLDER = UPLOAD_FOLDER / 'avatars'
    
    # Session security settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 7 days

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig if os.environ.get('FLASK_ENV') == 'development' else ProductionConfig
}
