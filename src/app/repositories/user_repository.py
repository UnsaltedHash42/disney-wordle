"""User repository with user-specific queries."""

import logging
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from .base_repository import BaseRepository
from ..models.user import User

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User model with specific query methods."""
    
    def __init__(self):
        """Initialize user repository."""
        super().__init__(User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        try:
            return self.session.query(User).filter(
                User.email == email.lower()
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by email {email}: {e}")
            self.session.rollback()
            return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            return self.session.query(User).filter(
                User.username == username.lower()
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user by username {username}: {e}")
            self.session.rollback()
            return None
    
    def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        try:
            return self.session.query(User).filter(
                User.email == email.lower()
            ).count() > 0
        except SQLAlchemyError as e:
            logger.error(f"Error checking email existence {email}: {e}")
            return False
    
    def username_exists(self, username: str) -> bool:
        """Check if username is already taken."""
        try:
            return self.session.query(User).filter(
                User.username == username.lower()
            ).count() > 0
        except SQLAlchemyError as e:
            logger.error(f"Error checking username existence {username}: {e}")
            return False 