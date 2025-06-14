"""Flask application factory."""

import logging
from typing import Optional

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import get_flask_config
from .database import init_db
from .middleware.security import SecurityMiddleware
from .middleware.rate_limiting import RateLimitConfig


def create_app(config_name: Optional[str] = None) -> Flask:
    """Create and configure Flask application.
    
    Args:
        config_name: Configuration environment name
        
    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config = get_flask_config()
    app.config.update(config)
    # Enable JWTs in cookies for SSR compatibility
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Disable CSRF for local/dev SSR
    
    # Initialize extensions
    init_extensions(app)
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Configure logging
    configure_logging(app)
    print_routes(app)
    
    return app


def init_extensions(app: Flask) -> None:
    """Initialize Flask extensions.
    
    Args:
        app: Flask application instance
    """
    # JWT Manager
    jwt = JWTManager(app)
    
    # CORS - Updated for our app URL
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://127.0.0.1:8000", "http://localhost:8000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Enhanced Rate Limiter
    limiter = RateLimitConfig.init_limiter(app)
    
    # Apply rate limit error handler
    app.errorhandler(429)(RateLimitConfig.get_error_handler())
    
    # Security Middleware
    security = SecurityMiddleware(app)
    
    # Store extensions in app for access in other modules
    app.extensions['jwt'] = jwt
    app.extensions['limiter'] = limiter
    app.extensions['security'] = security


def register_blueprints(app: Flask) -> None:
    """Register application blueprints.
    
    Args:
        app: Flask application instance
    """
    # Import blueprints here to avoid circular imports
    from .api.auth import auth_bp
    from .api.game import game_bp
    from .api.stats import stats_bp
    from .api.health import health_bp
    from .routes.main import main_bp
    
    # Register API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(health_bp)
    
    # Register main template routes
    app.register_blueprint(main_bp)


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers.
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'data': None
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'data': None
        }), 500
    
    @app.errorhandler(ValueError)
    def validation_error(error):
        """Handle validation errors."""
        return jsonify({
            'success': False,
            'error': str(error),
            'data': None
        }), 400


def configure_logging(app: Flask) -> None:
    """Configure application logging.
    
    Args:
        app: Flask application instance
    """
    if not app.debug and not app.testing:
        # Configure file logging for production
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(name)s %(levelname)s: %(message)s'
        )
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Wordle application startup')


def print_routes(app: Flask) -> None:
    """Print all registered routes for debugging."""
    print("\nRegistered routes:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        print(f"{rule.endpoint:30s} {methods:20s} {rule}")
    print() 