"""Tests for AuthService business logic."""

import pytest
from src.app.services.auth_service import AuthService
from src.app.models import User
from src.app.database import db


class TestAuthService:
    """Test AuthService functionality."""
    
    @pytest.fixture
    def auth_service(self, app):
        """Create AuthService instance for testing."""
        with app.app_context():
            yield AuthService()
    
    def test_register_user_success(self, auth_service, app, sample_user_data):
        """Test successful user registration."""
        with app.app_context():
            user = auth_service.register_user(sample_user_data)
            
            assert user is not None
            assert user.username == sample_user_data["username"]
            assert user.email == sample_user_data["email"]
            assert user.check_password(sample_user_data["password"])
            assert user.email_verified is False
            assert user.is_active is True
    
    def test_register_user_missing_fields(self, auth_service, app):
        """Test registration with missing required fields."""
        with app.app_context():
            incomplete_data = [
                {"username": "test", "email": "test@example.com"},  # Missing password
                {"username": "test", "password": "TestPass123"},    # Missing email
                {"email": "test@example.com", "password": "TestPass123"},  # Missing username
                {}  # Missing all fields
            ]
            
            for data in incomplete_data:
                with pytest.raises(ValueError, match="required"):
                    auth_service.register_user(data)
    
    def test_register_user_duplicate_email(self, auth_service, app, sample_user_data):
        """Test registration with duplicate email."""
        with app.app_context():
            # Register first user
            auth_service.register_user(sample_user_data)
            
            # Try to register with same email
            duplicate_data = {
                "username": "differentuser",
                "email": sample_user_data["email"],
                "password": "DifferentPass123"
            }
            
            with pytest.raises(ValueError, match="already registered"):
                auth_service.register_user(duplicate_data)
    
    def test_register_user_duplicate_username(self, auth_service, app, sample_user_data):
        """Test registration with duplicate username."""
        with app.app_context():
            # Register first user
            auth_service.register_user(sample_user_data)
            
            # Try to register with same username
            duplicate_data = {
                "username": sample_user_data["username"],
                "email": "different@example.com",
                "password": "DifferentPass123"
            }
            
            with pytest.raises(ValueError, match="already taken"):
                auth_service.register_user(duplicate_data)
    
    def test_register_user_invalid_password(self, auth_service, app):
        """Test registration with invalid password."""
        with app.app_context():
            invalid_data = {
                "username": "testuser",
                "email": "test@example.com",
                "password": "weak"  # Too weak password
            }
            
            with pytest.raises(ValueError, match="complexity requirements"):
                auth_service.register_user(invalid_data)
    
    def test_authenticate_user_success(self, auth_service, app, sample_user_data):
        """Test successful user authentication."""
        with app.app_context():
            # Register user first
            registered_user = auth_service.register_user(sample_user_data)
            
            # Authenticate user
            authenticated_user = auth_service.authenticate_user(
                sample_user_data["email"],
                sample_user_data["password"]
            )
            
            assert authenticated_user is not None
            assert authenticated_user.id == registered_user.id
            assert authenticated_user.email == sample_user_data["email"]
    
    def test_authenticate_user_wrong_email(self, auth_service, app, sample_user_data):
        """Test authentication with wrong email."""
        with app.app_context():
            # Register user first
            auth_service.register_user(sample_user_data)
            
            # Try with wrong email
            with pytest.raises(ValueError, match="Invalid email or password"):
                auth_service.authenticate_user(
                    "wrong@example.com",
                    sample_user_data["password"]
                )
    
    def test_authenticate_user_wrong_password(self, auth_service, app, sample_user_data):
        """Test authentication with wrong password."""
        with app.app_context():
            # Register user first
            auth_service.register_user(sample_user_data)
            
            # Try with wrong password
            with pytest.raises(ValueError, match="Invalid email or password"):
                auth_service.authenticate_user(
                    sample_user_data["email"],
                    "WrongPassword123"
                )
    
    def test_authenticate_user_inactive(self, auth_service, app, sample_user_data):
        """Test authentication with inactive user."""
        with app.app_context():
            # Register user first
            user = auth_service.register_user(sample_user_data)
            
            # Deactivate user
            user.is_active = False
            db.session.commit()
            
            # Try to authenticate
            with pytest.raises(ValueError, match="deactivated"):
                auth_service.authenticate_user(
                    sample_user_data["email"],
                    sample_user_data["password"]
                )
    
    def test_authenticate_user_missing_credentials(self, auth_service, app):
        """Test authentication with missing credentials."""
        with app.app_context():
            # Missing email
            with pytest.raises(ValueError, match="required"):
                auth_service.authenticate_user("", "password")
            
            # Missing password
            with pytest.raises(ValueError, match="required"):
                auth_service.authenticate_user("test@example.com", "")
    
    def test_get_user_by_id(self, auth_service, app, sample_user_data):
        """Test getting user by ID."""
        with app.app_context():
            # Register user first
            registered_user = auth_service.register_user(sample_user_data)
            
            # Get user by ID
            found_user = auth_service.get_user_by_id(registered_user.id)
            
            assert found_user is not None
            assert found_user.id == registered_user.id
            assert found_user.email == sample_user_data["email"]
    
    def test_get_user_by_id_not_found(self, auth_service, app):
        """Test getting user by non-existent ID."""
        with app.app_context():
            user = auth_service.get_user_by_id(99999)
            assert user is None
    
    def test_get_user_by_email(self, auth_service, app, sample_user_data):
        """Test getting user by email."""
        with app.app_context():
            # Register user first
            registered_user = auth_service.register_user(sample_user_data)
            
            # Get user by email
            found_user = auth_service.get_user_by_email(sample_user_data["email"])
            
            assert found_user is not None
            assert found_user.id == registered_user.id
            assert found_user.email == sample_user_data["email"]
    
    def test_get_user_by_email_not_found(self, auth_service, app):
        """Test getting user by non-existent email."""
        with app.app_context():
            user = auth_service.get_user_by_email("nonexistent@example.com")
            assert user is None
    
    def test_change_password_success(self, auth_service, app, sample_user_data):
        """Test successful password change."""
        with app.app_context():
            # Register user first
            user = auth_service.register_user(sample_user_data)
            old_password = sample_user_data["password"]
            new_password = "NewPassword123"
            
            # Change password
            success = auth_service.change_password(
                user.id,
                old_password,
                new_password
            )
            
            assert success is True
            
            # Verify old password no longer works
            updated_user = auth_service.get_user_by_id(user.id)
            assert updated_user.check_password(old_password) is False
            assert updated_user.check_password(new_password) is True
    
    def test_change_password_wrong_current(self, auth_service, app, sample_user_data):
        """Test password change with wrong current password."""
        with app.app_context():
            # Register user first
            user = auth_service.register_user(sample_user_data)
            
            # Try to change with wrong current password
            with pytest.raises(ValueError, match="Current password is incorrect"):
                auth_service.change_password(
                    user.id,
                    "WrongCurrentPass123",
                    "NewPassword123"
                )
    
    def test_change_password_invalid_new_password(self, auth_service, app, sample_user_data):
        """Test password change with invalid new password."""
        with app.app_context():
            # Register user first
            user = auth_service.register_user(sample_user_data)
            
            # Try to change to weak password
            with pytest.raises(ValueError, match="complexity requirements"):
                auth_service.change_password(
                    user.id,
                    sample_user_data["password"],
                    "weak"
                ) 