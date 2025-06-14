"""Tests for User model validation and methods."""

import pytest
from src.app.models import User
from src.app.database import db


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, app):
        """Test basic user creation."""
        with app.app_context():
            user = User(
                username="testuser",
                email="test@example.com"
            )
            user.set_password("TestPass123")
            
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.password_hash is not None
            assert user.email_verified is False
            assert user.is_active is True
    
    def test_email_validation_valid(self, app):
        """Test valid email addresses."""
        with app.app_context():
            valid_emails = [
                "test@example.com",
                "user.name@domain.co.uk",
                "test123@test-domain.org"
            ]
            
            for email in valid_emails:
                user = User(username="test", email=email)
                assert user.email == email.lower()
    
    def test_email_validation_invalid(self, app):
        """Test invalid email addresses."""
        with app.app_context():
            invalid_emails = [
                "invalid-email",
                "@domain.com",
                "test@",
                "test.domain.com"
            ]
            
            for email in invalid_emails:
                with pytest.raises(ValueError, match="Invalid email format"):
                    User(username="test", email=email)
    
    def test_username_validation_valid(self, app):
        """Test valid usernames."""
        with app.app_context():
            valid_usernames = [
                "testuser",
                "user123",
                "test_user",
                "test-user"
            ]
            
            for username in valid_usernames:
                user = User(username=username, email="test@example.com")
                assert user.username == username.lower()
    
    def test_username_validation_invalid(self, app):
        """Test invalid usernames."""
        with app.app_context():
            # Too short
            with pytest.raises(ValueError, match="at least 3 characters"):
                User(username="ab", email="test@example.com")
            
            # Too long
            with pytest.raises(ValueError, match="less than 50 characters"):
                User(username="a" * 51, email="test@example.com")
            
            # Invalid characters
            with pytest.raises(ValueError, match="letters, numbers, hyphens, and underscores"):
                User(username="test@user", email="test@example.com")
    
    def test_password_validation_valid(self, app):
        """Test valid passwords."""
        with app.app_context():
            user = User(username="test", email="test@example.com")
            
            valid_passwords = [
                "TestPass123",
                "MyPassword1",
                "Complex9Pass"
            ]
            
            for password in valid_passwords:
                user.set_password(password)
                assert user.password_hash is not None
    
    def test_password_validation_invalid(self, app):
        """Test invalid passwords."""
        with app.app_context():
            user = User(username="test", email="test@example.com")
            
            invalid_passwords = [
                "short",          # Too short
                "nouppercase1",   # No uppercase
                "NOLOWERCASE1",   # No lowercase  
                "NoNumbers",      # No numbers
            ]
            
            for password in invalid_passwords:
                with pytest.raises(ValueError, match="complexity requirements"):
                    user.set_password(password)
    
    def test_password_hashing(self, app):
        """Test password hashing functionality."""
        with app.app_context():
            user = User(username="test", email="test@example.com")
            password = "TestPass123"
            
            user.set_password(password)
            
            # Password should be hashed, not stored as plain text
            assert user.password_hash != password
            assert len(user.password_hash) > 50  # bcrypt hash length
            
            # Should verify correct password
            assert user.check_password(password) is True
            
            # Should reject incorrect password
            assert user.check_password("wrongpassword") is False
    
    def test_to_dict_excludes_sensitive(self, app):
        """Test to_dict method excludes sensitive information."""
        with app.app_context():
            user = User(username="test", email="test@example.com")
            user.set_password("TestPass123")
            
            user_dict = user.to_dict()
            
            # Should include public fields
            assert "id" in user_dict
            assert "username" in user_dict
            assert "email" in user_dict
            assert "email_verified" in user_dict
            assert "is_active" in user_dict
            
            # Should exclude sensitive fields
            assert "password_hash" not in user_dict
    
    def test_user_repr(self, app):
        """Test user string representation."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("TestPass123")  # Password required for database
            db.session.add(user)
            db.session.commit()
            
            repr_str = repr(user)
            assert "User" in repr_str
            assert "testuser" in repr_str
            assert "test@example.com" in repr_str 