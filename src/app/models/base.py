"""Base model and mixins for SQLAlchemy models."""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, Integer, DateTime, Boolean, func

from ..database import db


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    
    def soft_delete(self) -> None:
        """Mark record as deleted without removing from database."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()


class BaseModel(db.Model, TimestampMixin):
    """Abstract base model with common fields and methods."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    def to_dict(self, exclude_sensitive: bool = True) -> Dict[str, Any]:
        """Convert model to dictionary representation.
        
        Args:
            exclude_sensitive: Whether to exclude sensitive fields like passwords
            
        Returns:
            Dictionary representation of the model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            
            # Convert datetime objects to ISO format
            if isinstance(value, datetime):
                value = value.isoformat()
            
            # Skip sensitive fields if requested
            if exclude_sensitive and column.name in ['password_hash', 'password']:
                continue
                
            result[column.name] = value
            
        return result
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model attributes from dictionary.
        
        Args:
            data: Dictionary with field names and values to update
        """
        for key, value in data.items():
            if hasattr(self, key) and not key.startswith('_'):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


# Keep the old Base class for backward compatibility (if needed)
Base = db.Model 