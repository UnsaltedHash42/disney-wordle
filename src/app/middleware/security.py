"""Security middleware for adding security headers and protections."""

from flask import Flask, request, g
import time
from typing import Dict, Any


class SecurityMiddleware:
    """Middleware for adding security headers and protections."""
    
    def __init__(self, app: Flask = None):
        """Initialize security middleware."""
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """Initialize security middleware with Flask app."""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        # Store request start time for performance monitoring
        @app.before_request
        def start_timer():
            g.start_time = time.time()
    
    def _before_request(self) -> None:
        """Process request before handling."""
        # Add request ID for tracking
        g.request_id = self._generate_request_id()
        
        # Log suspicious requests
        if self._is_suspicious_request():
            app = self.app or request.app
            app.logger.warning(f"Suspicious request: {request.remote_addr} - {request.url}")
    
    def _after_request(self, response):
        """Add security headers to response."""
        # Security headers
        security_headers = {
            # Prevent XSS attacks
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            
            # Content Security Policy (TEMP: allow 'unsafe-eval' for Alpine.js dev)
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
                "font-src 'self' https:; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            ),
            
            # HTTPS enforcement (in production)
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            
            # Referrer policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Permissions policy
            'Permissions-Policy': (
                'accelerometer=(), camera=(), geolocation=(), '
                'gyroscope=(), magnetometer=(), microphone=(), '
                'payment=(), usb=()'
            ),
            
            # Cache control for security
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
        
        # Add security headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Add performance headers
        if hasattr(g, 'start_time'):
            response_time = time.time() - g.start_time
            response.headers['X-Response-Time'] = f"{response_time:.3f}s"
        
        # Add request ID header
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        # CORS headers for API endpoints
        if request.path.startswith('/api/'):
            response.headers['Access-Control-Allow-Origin'] = 'http://127.0.0.1:8000'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Max-Age'] = '3600'
        
        return response
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracking."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _is_suspicious_request(self) -> bool:
        """Check if request is suspicious."""
        # Check for common attack patterns
        suspicious_patterns = [
            'script>', '<iframe', 'javascript:', 'vbscript:',
            'onload=', 'onerror=', 'alert(', 'document.cookie',
            '../', '..\\', '/etc/passwd', '/admin', '/config'
        ]
        
        # Check URL and query parameters
        full_url = request.url.lower()
        for pattern in suspicious_patterns:
            if pattern in full_url:
                return True
        
        # Check User-Agent for bots (basic check)
        user_agent = request.headers.get('User-Agent', '').lower()
        bot_indicators = ['bot', 'crawler', 'spider', 'scraper']
        if any(indicator in user_agent for indicator in bot_indicators):
            return True
        
        # Check for too many requests from same IP (basic rate limiting)
        # This is a simple check - in production, use Redis or similar
        if not hasattr(g, 'ip_requests'):
            g.ip_requests = {}
        
        client_ip = request.remote_addr
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        g.ip_requests = {
            ip: [req_time for req_time in times if current_time - req_time < 60]
            for ip, times in g.ip_requests.items()
        }
        
        # Count current IP requests
        if client_ip not in g.ip_requests:
            g.ip_requests[client_ip] = []
        
        g.ip_requests[client_ip].append(current_time)
        
        # Flag if more than 100 requests per minute
        if len(g.ip_requests[client_ip]) > 100:
            return True
        
        return False