"""
Shared Extension Instances

Extensions are instantiated here WITHOUT an app, then bound to the
app later inside the application factory (app/__init__.py) via
`extension.init_app(app)`.

Keeping them here (instead of directly in __init__.py) prevents
circular imports: models.py and blueprint route files can safely
`from app.extensions import db` without importing the factory itself.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from authlib.integrations.flask_client import OAuth

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
oauth = OAuth()  # powers "Continue with Google" on the login page

# --- Flask-Login configuration ---
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"
