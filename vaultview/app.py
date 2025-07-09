from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import json
import os
import secrets
from vaultview.routes import main
from vaultview.auth.routes import auth
from vaultview.db import db
from vaultview.models import User

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app(*args, **kwargs):
    # Get the directory where this file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to the project root
    project_root = os.path.dirname(current_dir)
    
    app = Flask(__name__, 
                template_folder=os.path.join(project_root, 'templates'),
                static_folder=os.path.join(project_root, 'static'),
                instance_path=os.path.join(project_root, 'instance'))
    
    # Load configuration from instance/config.py
    try:
        app.config.from_pyfile('config.py')
    except FileNotFoundError:
        # Fallback configuration if config file doesn't exist
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///vaultview.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['WTF_CSRF_ENABLED'] = True
        app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)
    CSRFProtect(app)
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth)
    
    # Register custom Jinja2 filter
    @app.template_filter('from_json')
    def from_json_filter(value):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    # Start notification service
    with app.app_context():
        from vaultview.notifications import start_notification_service
        start_notification_service()
    
    return app