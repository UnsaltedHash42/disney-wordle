"""Health check endpoint for monitoring."""

from flask import Blueprint, jsonify
from ..database import db

health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'service': 'wordle-api',
            'database': 'connected'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'wordle-api',
            'database': 'disconnected',
            'error': str(e)
        }), 503


@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """Basic metrics endpoint for monitoring."""
    try:
        from ..utils.caching import CacheManager
        
        cache_stats = CacheManager.get_cache_stats()
        
        # Count total users and games
        from ..models.user import User
        from ..models.game import GameSession
        
        total_users = db.session.query(User).count()
        total_games = db.session.query(GameSession).count()
        
        return jsonify({
            'users': {
                'total': total_users
            },
            'games': {
                'total': total_games
            },
            'cache': cache_stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Unable to fetch metrics',
            'message': str(e)
        }), 500