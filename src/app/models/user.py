"""User model for authentication and user management."""

import re
from typing import Optional

import bcrypt
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import validates, relationship

from .base import BaseModel


class User(BaseModel):
    """User model with authentication capabilities."""
    
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    game_sessions = relationship("GameSession", back_populates="user", cascade="all, delete-orphan")
    user_stats = relationship("UserStats", back_populates="user", cascade="all, delete-orphan")
    
    @validates('email')
    def validate_email(self, key: str, address: str) -> str:
        """Validate email format.
        
        Args:
            key: Field name being validated
            address: Email address to validate
            
        Returns:
            Validated email address
            
        Raises:
            ValueError: If email format is invalid
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, address):
            raise ValueError("Invalid email format")
        return address.lower()
    
    @validates('username')
    def validate_username(self, key: str, username: str) -> str:
        """Validate username format.
        
        Args:
            key: Field name being validated
            username: Username to validate
            
        Returns:
            Validated username
            
        Raises:
            ValueError: If username format is invalid
        """
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(username) > 50:
            raise ValueError("Username must be less than 50 characters long")
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValueError("Username can only contain letters, numbers, hyphens, and underscores")
        return username.lower()
    
    def set_password(self, password: str) -> None:
        """Hash and set user password.
        
        Args:
            password: Plain text password to hash
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if not self._validate_password_strength(password):
            raise ValueError("Password does not meet complexity requirements")
        
        # Hash password with bcrypt (12+ rounds)
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @staticmethod
    def _validate_password_strength(password: str) -> bool:
        """Validate password meets complexity requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets requirements, False otherwise
        """
        # Password must be at least 8 characters long
        if len(password) < 8:
            return False
        
        # Password must contain at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            return False
        
        # Password must contain at least one lowercase letter
        if not re.search(r'[a-z]', password):
            return False
        
        # Password must contain at least one digit
        if not re.search(r'\d', password):
            return False
        
        return True
    
    def to_dict(self, exclude_sensitive: bool = True) -> dict:
        """Convert user to dictionary, excluding sensitive data by default.
        
        Args:
            exclude_sensitive: Whether to exclude password hash and other sensitive fields
            
        Returns:
            Dictionary representation of user
        """
        result = super().to_dict(exclude_sensitive=exclude_sensitive)
        
        # Always exclude password hash from serialization
        result.pop('password_hash', None)
        
        return result
    
    def __repr__(self) -> str:
        """String representation of user."""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>" 