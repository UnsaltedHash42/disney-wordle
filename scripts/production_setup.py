#!/usr/bin/env python3
"""
Production setup script for Wordle application.
Configures environment for production deployment.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))


def create_production_env():
    """Create production environment file."""
    env_content = """# Production Environment Configuration
# Copy this to .env and update with your production values

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/wordle_production
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production
JWT_ACCESS_TOKEN_EXPIRES=15  # minutes
JWT_REFRESH_TOKEN_EXPIRES=30  # days

# Security Configuration
BCRYPT_LOG_ROUNDS=12
RATE_LIMIT_STORAGE_URI=redis://localhost:6379/0

# Application Configuration
DEFAULT_GAME_MODE=classic
MAX_GUESSES=6
WORD_LENGTH=5

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/wordle/app.log

# Performance Configuration
CACHE_TYPE=redis
CACHE_REDIS_URL=redis://localhost:6379/1
CACHE_DEFAULT_TIMEOUT=300

# External Services
SENTRY_DSN=your-sentry-dsn-for-error-tracking
"""
    
    with open('.env.production', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env.production template")


def create_dockerfile():
    """Create Dockerfile for containerized deployment."""
    dockerfile_content = """# Dockerfile for Wordle Web Application
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' wordle
RUN chown -R wordle:wordle /app
USER wordle

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "sync", "--timeout", "120", "application:app"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    print("✅ Created Dockerfile")


def create_docker_compose():
    """Create Docker Compose file for full stack deployment."""
    compose_content = """version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://wordle:password@db:5432/wordle
      - CACHE_REDIS_URL=redis://redis:6379/1
      - RATE_LIMIT_STORAGE_URI=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/var/log/wordle
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=wordle
      - POSTGRES_USER=wordle
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
"""
    
    with open('docker-compose.prod.yml', 'w') as f:
        f.write(compose_content)
    
    print("✅ Created docker-compose.prod.yml")


def create_nginx_config():
    """Create Nginx configuration for reverse proxy."""
    nginx_content = """events {
    worker_connections 1024;
}

http {
    upstream wordle_app {
        server web:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;

    server {
        listen 80;
        server_name your-domain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/ssl/certs/fullchain.pem;
        ssl_certificate_key /etc/ssl/certs/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # Gzip compression
        gzip on;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

        # API routes with rate limiting
        location /api/auth/ {
            limit_req zone=auth burst=10 nodelay;
            proxy_pass http://wordle_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://wordle_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files and main app
        location / {
            proxy_pass http://wordle_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
"""
    
    with open('nginx.conf', 'w') as f:
        f.write(nginx_content)
    
    print("✅ Created nginx.conf")


def create_systemd_service():
    """Create systemd service file for Linux deployment."""
    service_content = """[Unit]
Description=Wordle Web Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=wordle
Group=wordle
WorkingDirectory=/opt/wordle
Environment=PATH=/opt/wordle/venv/bin
ExecStart=/opt/wordle/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 4 application:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open('wordle.service', 'w') as f:
        f.write(service_content)
    
    print("✅ Created wordle.service")


def create_requirements_prod():
    """Create production requirements file."""
    prod_requirements = """# Production requirements for Wordle application
Flask==2.3.3
SQLAlchemy==2.0.23
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-JWT-Extended==4.6.0
Flask-CORS==4.0.0
Flask-Limiter==3.5.0
psycopg2-binary==2.9.9
bcrypt==4.1.2
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
redis==5.0.1
gunicorn==21.2.0
sentry-sdk[flask]==1.38.0
requests==2.31.0
"""
    
    with open('requirements.prod.txt', 'w') as f:
        f.write(prod_requirements)
    
    print("✅ Created requirements.prod.txt")


def create_health_check():
    """Create health check endpoint."""
    health_check_content = """\"\"\"Health check endpoint for monitoring.\"\"\"

from flask import Blueprint, jsonify
from ..database import db

health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health_check():
    \"\"\"Health check endpoint for load balancers and monitoring.\"\"\"
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
    \"\"\"Basic metrics endpoint for monitoring.\"\"\"
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
"""
    
    # Create health check module
    os.makedirs('src/app/api', exist_ok=True)
    with open('src/app/api/health.py', 'w') as f:
        f.write(health_check_content)
    
    print("✅ Created health check endpoint")


def main():
    """Set up production environment."""
    print("🚀 Setting up Wordle for production deployment...")
    print("=" * 50)
    
    create_production_env()
    create_dockerfile()
    create_docker_compose()
    create_nginx_config()
    create_systemd_service()
    create_requirements_prod()
    create_health_check()
    
    print("\n" + "=" * 50)
    print("✅ Production setup completed!")
    print("\n📋 Next steps:")
    print("1. Copy .env.production to .env and update with your values")
    print("2. Install production requirements: pip install -r requirements.prod.txt")
    print("3. Set up SSL certificates in ./ssl/ directory")
    print("4. Update nginx.conf with your domain name")
    print("5. Run: docker-compose -f docker-compose.prod.yml up -d")
    print("\n🔒 Security checklist:")
    print("- Change all default passwords and secret keys")
    print("- Set up SSL certificates (Let's Encrypt recommended)")
    print("- Configure firewall rules")
    print("- Set up monitoring and logging")
    print("- Configure regular database backups")


if __name__ == "__main__":
    main()