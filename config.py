import os
import secrets
from datetime import timedelta

class Config:
    # Use a strong default secret key that's different from the dev key
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY') or ''
    STATIC_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
    TEMPLATES_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Development settings
    DEBUG = False
    TESTING = False
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False

class DevelopmentConfig(Config):
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    EXPLAIN_TEMPLATE_LOADING = True
    PRESERVE_CONTEXT_ON_EXCEPTION = True

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS in production
    EXPLAIN_TEMPLATE_LOADING = False
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 