"""Authentication service with business logic."""

import logging
from typing import Dict, Any, Optional

from ..models.user import User
from ..repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication business logic."""
    
    def __init__(self):
        """Initialize authentication service."""
        self.user_repo = UserRepository()
    
    def register_user(self, data: Dict[str, Any]) -> User:
        """Register a new user.
        
        Args:
            data: Dictionary containing username, email, and password
            
        Returns:
            Created User instance
            
        Raises:
            ValueError: If validation fails or user already exists
        """
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Validate required fields
        if not all([username, email, password]):
            raise ValueError("Username, email, and password are required")
        
        # Check if email already exists
        if self.user_repo.email_exists(email):
            raise ValueError("Email address is already registered")
        
        # Check if username already exists
        if self.user_repo.username_exists(username):
            raise ValueError("Username is already taken")
        
        # Create new user
        try:
            user = User(
                username=username,
                email=email
            )
            user.set_password(password)
            
            # Save user to database
            created_user = self.user_repo.create({
                'username': user.username,
                'email': user.email,
                'password_hash': user.password_hash,
                'email_verified': False,
                'is_active': True
            })
            
            if not created_user:
                raise ValueError("Failed to create user account")
            
            logger.info(f"New user registered: {created_user.username}")
            return created_user
            
        except ValueError as e:
            # Re-raise validation errors
            raise e
        except Exception as e:
            logger.error(f"Error registering user {username}: {e}")
            raise ValueError("Registration failed. Please try again.")
    
    def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Authenticated User instance
            
        Raises:
            ValueError: If authentication fails
        """
        if not email or not password:
            raise ValueError("Email and password are required")
        
        # Get user by email
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is deactivated")
        
        # Verify password
        if not user.check_password(password):
            raise ValueError("Invalid email or password")
        
        logger.info(f"User authenticated: {user.username}")
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            User instance or None if not found
        """
        return self.user_repo.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User instance or None if not found
        """
        return self.user_repo.get_by_email(email)
    
    def verify_email(self, user_id: int) -> bool:
        """Mark user's email as verified.
        
        Args:
            user_id: User's ID
            
        Returns:
            True if verification successful, False otherwise
        """
        try:
            success = self.user_repo.verify_email(user_id)
            if success:
                logger.info(f"Email verified for user ID: {user_id}")
            return success
        except Exception as e:
            logger.error(f"Error verifying email for user {user_id}: {e}")
            return False
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user's password.
        
        Args:
            user_id: User's ID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password changed successfully, False otherwise
            
        Raises:
            ValueError: If validation fails
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify current password
        if not user.check_password(current_password):
            raise ValueError("Current password is incorrect")
        
        # Set new password
        try:
            user.set_password(new_password)
            
            # Update in database
            updated_user = self.user_repo.update(user_id, {
                'password_hash': user.password_hash
            })
            
            if updated_user:
                logger.info(f"Password changed for user: {user.username}")
                return True
            return False
            
        except ValueError as e:
            # Re-raise validation errors
            raise e
        except Exception as e:
            logger.error(f"Error changing password for user {user_id}: {e}")
            return False 