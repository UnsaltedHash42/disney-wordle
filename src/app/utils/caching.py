"""Caching utilities for performance optimization."""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, Callable
from functools import wraps
from flask import current_app, g
import time


class SimpleCache:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self):
        """Initialize cache."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_cleanup = time.time()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        self._cleanup_if_needed()
        
        if key in self._cache:
            entry = self._cache[key]
            if entry['expires_at'] > time.time():
                entry['last_accessed'] = time.time()
                return entry['value']
            else:
                del self._cache[key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value in cache with TTL."""
        self._cleanup_if_needed()
        
        self._cache[key] = {
            'value': value,
            'expires_at': time.time() + ttl,
            'last_accessed': time.time()
        }
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def _cleanup_if_needed(self) -> None:
        """Clean up expired entries periodically."""
        current_time = time.time()
        
        # Only cleanup every 5 minutes
        if current_time - self._last_cleanup < 300:
            return
        
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry['expires_at'] < current_time
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        self._last_cleanup = current_time


# Global cache instance
app_cache = SimpleCache()


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            func_key = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = app_cache.get(func_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            app_cache.set(func_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_daily_puzzle(game_mode: str, date: str):
    """Cache daily puzzle for better performance."""
    key = f"daily_puzzle:{game_mode}:{date}"
    return app_cache.get(key)


def set_daily_puzzle_cache(game_mode: str, date: str, puzzle_data: Any):
    """Set daily puzzle cache (expires at end of day)."""
    key = f"daily_puzzle:{game_mode}:{date}"
    
    # Calculate TTL until end of day
    now = datetime.utcnow()
    end_of_day = datetime(now.year, now.month, now.day, 23, 59, 59)
    ttl = int((end_of_day - now).total_seconds())
    
    app_cache.set(key, puzzle_data, ttl)


def cache_user_stats(user_id: int, game_mode: str = None):
    """Cache user statistics."""
    if game_mode:
        key = f"user_stats:{user_id}:{game_mode}"
    else:
        key = f"user_stats:{user_id}:all"
    
    return app_cache.get(key)


def set_user_stats_cache(user_id: int, stats_data: Any, game_mode: str = None, ttl: int = 600):
    """Set user statistics cache."""
    if game_mode:
        key = f"user_stats:{user_id}:{game_mode}"
    else:
        key = f"user_stats:{user_id}:all"
    
    app_cache.set(key, stats_data, ttl)


def invalidate_user_stats_cache(user_id: int):
    """Invalidate user statistics cache after game completion."""
    # Clear both specific mode and all stats caches
    app_cache.delete(f"user_stats:{user_id}:classic")
    app_cache.delete(f"user_stats:{user_id}:disney")
    app_cache.delete(f"user_stats:{user_id}:all")


def cache_leaderboard(game_mode: str, metric: str, limit: int = 10):
    """Cache leaderboard data."""
    key = f"leaderboard:{game_mode}:{metric}:{limit}"
    return app_cache.get(key)


def set_leaderboard_cache(game_mode: str, metric: str, limit: int, leaderboard_data: Any, ttl: int = 300):
    """Set leaderboard cache."""
    key = f"leaderboard:{game_mode}:{metric}:{limit}"
    app_cache.set(key, leaderboard_data, ttl)


def cache_word_validation(word: str, game_mode: str):
    """Cache word validation results."""
    key = f"word_valid:{game_mode}:{word.upper()}"
    return app_cache.get(key)


def set_word_validation_cache(word: str, game_mode: str, is_valid: bool, ttl: int = 86400):
    """Set word validation cache (cache for 24 hours)."""
    key = f"word_valid:{game_mode}:{word.upper()}"
    app_cache.set(key, is_valid, ttl)


class CacheManager:
    """Manager for coordinating cache operations."""
    
    @staticmethod
    def warm_cache():
        """Warm up cache with frequently accessed data."""
        current_app.logger.info("Warming up cache...")
        
        # Cache today's date for puzzle lookups
        today = datetime.utcnow().date().isoformat()
        
        # You could pre-cache daily puzzles here
        # This would be called at app startup
        
    @staticmethod
    def clear_expired():
        """Clear expired cache entries."""
        app_cache._cleanup_if_needed()
    
    @staticmethod
    def get_cache_stats():
        """Get cache statistics for monitoring."""
        return {
            'total_entries': len(app_cache._cache),
            'last_cleanup': app_cache._last_cleanup,
            'cache_size_bytes': len(str(app_cache._cache))
        }