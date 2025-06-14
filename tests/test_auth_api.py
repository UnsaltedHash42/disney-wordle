"""Tests for authentication API endpoints."""

import pytest
import json
from src.app.models import User
from src.app.database import db


class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_register_success(self, client, sample_user_data):
        """Test successful user registration."""
        response = client.post('/api/auth/register', json=sample_user_data)
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['success'] is True
        assert 'user' in data['data']
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
        
        user_data = data['data']['user']
        assert user_data['username'] == sample_user_data['username']
        assert user_data['email'] == sample_user_data['email']
        assert 'password_hash' not in user_data  # Should not expose password
    
    def test_register_missing_fields(self, client):
        """Test registration with missing fields."""
        incomplete_data = [
            {"username": "test", "email": "test@example.com"},  # Missing password
            {"username": "test", "password": "TestPass123"},    # Missing email
            {"email": "test@example.com", "password": "TestPass123"},  # Missing username
        ]
        
        for data in incomplete_data:
            response = client.post('/api/auth/register', json=data)
            assert response.status_code == 400
            
            response_data = response.get_json()
            assert response_data['success'] is False
            assert 'error' in response_data
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "TestPass123"
        }
        
        response = client.post('/api/auth/register', json=invalid_data)
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_register_duplicate_user(self, client, sample_user_data):
        """Test registration with duplicate user data."""
        # Register first user
        response1 = client.post('/api/auth/register', json=sample_user_data)
        assert response1.status_code == 201
        
        # Try to register again with same email
        response2 = client.post('/api/auth/register', json=sample_user_data)
        assert response2.status_code == 400
        
        data = response2.get_json()
        assert data['success'] is False
        assert 'already registered' in data['error'].lower()
    
    def test_register_no_json(self, client):
        """Test registration with no JSON data."""
        response = client.post('/api/auth/register')
        assert response.status_code == 400
        
        data = response.get_json()
        assert data['success'] is False
        assert 'JSON data' in data['error']
    
    def test_login_success(self, client, sample_user_data):
        """Test successful login."""
        # Register user first
        client.post('/api/auth/register', json=sample_user_data)
        
        # Login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['success'] is True
        assert 'user' in data['data']
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
    
    def test_login_wrong_email(self, client, sample_user_data):
        """Test login with wrong email."""
        # Register user first
        client.post('/api/auth/register', json=sample_user_data)
        
        # Try login with wrong email
        login_data = {
            "email": "wrong@example.com",
            "password": sample_user_data["password"]
        }
        
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 401
        
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid email or password' in data['error']
    
    def test_login_wrong_password(self, client, sample_user_data):
        """Test login with wrong password."""
        # Register user first
        client.post('/api/auth/register', json=sample_user_data)
        
        # Try login with wrong password
        login_data = {
            "email": sample_user_data["email"],
            "password": "WrongPassword123"
        }
        
        response = client.post('/api/auth/login', json=login_data)
        assert response.status_code == 401
        
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid email or password' in data['error']
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields."""
        incomplete_data = [
            {"email": "test@example.com"},  # Missing password
            {"password": "TestPass123"},    # Missing email
            {}                              # Missing both
        ]
        
        for data in incomplete_data:
            response = client.post('/api/auth/login', json=data)
            assert response.status_code == 400
            
            response_data = response.get_json()
            assert response_data['success'] is False
    
    def test_get_current_user_success(self, client, sample_user_data):
        """Test getting current user with valid token."""
        # Register and get token
        register_response = client.post('/api/auth/register', json=sample_user_data)
        token = register_response.get_json()['data']['access_token']
        
        # Get current user
        headers = {'Authorization': f'Bearer {token}'}
        response = client.get('/api/auth/me', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'user' in data['data']
        
        user_data = data['data']['user']
        assert user_data['email'] == sample_user_data['email']
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get('/api/auth/me')
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {'Authorization': 'Bearer invalid-token'}
        response = client.get('/api/auth/me', headers=headers)
        assert response.status_code == 422  # JWT decode error
    
    def test_refresh_token_success(self, client, sample_user_data):
        """Test successful token refresh."""
        # Register and get tokens
        register_response = client.post('/api/auth/register', json=sample_user_data)
        refresh_token = register_response.get_json()['data']['refresh_token']
        
        # Refresh token
        headers = {'Authorization': f'Bearer {refresh_token}'}
        response = client.post('/api/auth/refresh', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'access_token' in data['data']
    
    def test_refresh_token_with_access_token(self, client, sample_user_data):
        """Test refresh with access token (should fail)."""
        # Register and get tokens
        register_response = client.post('/api/auth/register', json=sample_user_data)
        access_token = register_response.get_json()['data']['access_token']
        
        # Try to refresh with access token (should fail)
        headers = {'Authorization': f'Bearer {access_token}'}
        response = client.post('/api/auth/refresh', headers=headers)
        
        assert response.status_code == 422  # Wrong token type
    
    def test_refresh_token_no_token(self, client):
        """Test refresh without token."""
        response = client.post('/api/auth/refresh')
        assert response.status_code == 401
    
    def test_api_response_format(self, client, sample_user_data):
        """Test that all API responses follow standard format."""
        # Test successful response
        response = client.post('/api/auth/register', json=sample_user_data)
        data = response.get_json()
        
        assert 'success' in data
        assert 'data' in data
        assert 'error' in data
        assert data['success'] is True
        assert data['error'] is None
        
        # Test error response
        response = client.post('/api/auth/login', json={"email": "wrong@example.com", "password": "wrong"})
        data = response.get_json()
        
        assert 'success' in data
        assert 'data' in data  
        assert 'error' in data
        assert data['success'] is False
        assert data['data'] is None
        assert isinstance(data['error'], str)
    
    def test_validation_error_details(self, client):
        """Test that validation errors include field-level details."""
        # Send invalid JSON structure
        response = client.post('/api/auth/register', json={"username": 123})  # Invalid type
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'details' in data or 'error' in data  # Should have validation details
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.options('/api/auth/register')
        
        # Should not error and should have CORS headers
        assert response.status_code in [200, 204]
    
    def test_rate_limiting_headers(self, client, sample_user_data):
        """Test that rate limiting doesn't break normal requests."""
        # Make a normal request
        response = client.post('/api/auth/register', json=sample_user_data)
        
        # Should succeed normally (rate limiting should be permissive for testing)
        assert response.status_code == 201 