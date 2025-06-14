"""Database connection and session management."""

from typing import Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from ..config import get_flask_config

# Initialize SQLAlchemy instance
db = SQLAlchemy()
migrate = Migrate()


def init_db(app: Flask) -> None:
    """Initialize database with Flask application.
    
    Args:
        app: Flask application instance
    """
    # Initialize extensions (config should already be set)
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models to register them with SQLAlchemy
    from ..models import User  # noqa: F401
    
    # Create tables in development mode (not during testing)
    with app.app_context():
        if app.config.get('DEBUG', False) and not app.config.get('TESTING', False):
            db.create_all()


def get_db_session():
    """Get database session for dependency injection.
    
    Returns:
        SQLAlchemy database session
    """
    return db.session 