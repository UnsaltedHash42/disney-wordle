"""Enhanced rate limiting configuration for different endpoints."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask


class RateLimitConfig:
    """Configuration for rate limiting different types of endpoints."""
    
    # Rate limit configurations for different endpoint types
    RATE_LIMITS = {
        # Authentication endpoints - stricter limits
        'auth_register': '5 per minute',
        'auth_login': '10 per minute', 
        'auth_refresh': '20 per minute',
        
        # Game endpoints - moderate limits
        'game_guess': '30 per minute',
        'game_daily': '60 per minute',
        'game_validate': '100 per minute',
        
        # Statistics endpoints - higher limits
        'stats_user': '200 per minute',
        'stats_leaderboard': '100 per minute',
        
        # General API - default limits
        'api_default': '500 per hour',
        
        # Frontend pages - generous limits
        'frontend_pages': '1000 per hour'
    }
    
    @staticmethod
    def init_limiter(app: Flask) -> Limiter:
        """Initialize and configure the rate limiter."""
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["1000 per hour", "100 per minute"],
            storage_uri="memory://",  # Use Redis in production
            headers_enabled=True,
            retry_after="http-date"
        )
        
        return limiter
    
    @staticmethod
    def apply_limits(limiter: Limiter, app: Flask) -> None:
        """Apply rate limits to specific endpoints."""
        
        # Authentication endpoints
        @limiter.limit(RateLimitConfig.RATE_LIMITS['auth_register'])
        def limit_register():
            pass
        
        @limiter.limit(RateLimitConfig.RATE_LIMITS['auth_login'])
        def limit_login():
            pass
        
        @limiter.limit(RateLimitConfig.RATE_LIMITS['auth_refresh'])
        def limit_refresh():
            pass
        
        # Apply limits to blueprints
        with app.app_context():
            # Get blueprints and apply limits
            for blueprint_name, blueprint in app.blueprints.items():
                if blueprint_name == 'auth_bp':
                    # Apply auth limits
                    for endpoint in ['register', 'login', 'refresh']:
                        if hasattr(blueprint, endpoint):
                            limiter.limit(
                                RateLimitConfig.RATE_LIMITS[f'auth_{endpoint}']
                            )(getattr(blueprint, endpoint))
                
                elif blueprint_name == 'game_bp':
                    # Apply game limits
                    for endpoint in ['guess', 'daily', 'validate']:
                        if hasattr(blueprint, endpoint):
                            limiter.limit(
                                RateLimitConfig.RATE_LIMITS[f'game_{endpoint}']
                            )(getattr(blueprint, endpoint))
                
                elif blueprint_name == 'stats_bp':
                    # Apply stats limits
                    limiter.limit(
                        RateLimitConfig.RATE_LIMITS['stats_user']
                    )(blueprint)
    
    @staticmethod
    def get_error_handler():
        """Get custom error handler for rate limit exceeded."""
        def ratelimit_handler(e):
            """Handle rate limit exceeded errors."""
            return {
                'success': False,
                'error': 'Rate limit exceeded. Please try again later.',
                'data': {
                    'retry_after': e.retry_after,
                    'limit': e.limit,
                    'reset_time': e.reset_time
                }
            }, 429
        
        return ratelimit_handler