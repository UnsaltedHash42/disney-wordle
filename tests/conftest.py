"""Pytest configuration and shared fixtures."""

import pytest
from src.app import create_app
from src.app.database import db
from src.app.models import User


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret-key",
        "SECRET_KEY": "test-secret"
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123"
    }


@pytest.fixture
def created_user(app, sample_user_data):
    """Create a user in the database for testing."""
    with app.app_context():
        user = User(
            username=sample_user_data["username"],
            email=sample_user_data["email"]
        )
        user.set_password(sample_user_data["password"])
        
        db.session.add(user)
        db.session.commit()
        
        # Refresh to get the ID
        db.session.refresh(user)
        yield user


@pytest.fixture
def auth_headers(client, sample_user_data):
    """Get authentication headers with JWT token."""
    # Register user
    response = client.post('/api/auth/register', json=sample_user_data)
    assert response.status_code == 201
    
    data = response.get_json()
    token = data['data']['access_token']
    
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def auth_client(client, auth_headers):
    """Client with authentication headers set."""
    client.environ_base['HTTP_AUTHORIZATION'] = auth_headers['Authorization']
    return client 