"""Base repository with common CRUD operations."""

import logging
from typing import Type, TypeVar, Generic, Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..database import get_db_session
from ..models.base import BaseModel

T = TypeVar('T', bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model_class: Type[T]):
        """Initialize repository with model class.
        
        Args:
            model_class: SQLAlchemy model class
        """
        self.model_class = model_class
        self.session = get_db_session()
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get model instance by ID.
        
        Args:
            id: Primary key ID
            
        Returns:
            Model instance or None if not found
        """
        try:
            return self.session.query(self.model_class).filter(
                self.model_class.id == id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model_class.__name__} by ID {id}: {e}")
            self.session.rollback()
            return None
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Get all model instances.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of model instances
        """
        try:
            query = self.session.query(self.model_class)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
                
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model_class.__name__}: {e}")
            self.session.rollback()
            return []
    
    def create(self, data: Dict[str, Any]) -> Optional[T]:
        """Create new model instance.
        
        Args:
            data: Dictionary with model field values
            
        Returns:
            Created model instance or None if failed
        """
        try:
            instance = self.model_class(**data)
            self.session.add(instance)
            self.session.commit()
            self.session.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            self.session.rollback()
            return None
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """Update model instance by ID.
        
        Args:
            id: Primary key ID
            data: Dictionary with field values to update
            
        Returns:
            Updated model instance or None if not found
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None
            
            instance.update_from_dict(data)
            self.session.commit()
            self.session.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model_class.__name__} {id}: {e}")
            self.session.rollback()
            return None
    
    def delete(self, id: int) -> bool:
        """Delete model instance by ID.
        
        Args:
            id: Primary key ID
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False
            
            self.session.delete(instance)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model_class.__name__} {id}: {e}")
            self.session.rollback()
            return False
    
    def count(self) -> int:
        """Count total number of model instances.
        
        Returns:
            Total count of instances
        """
        try:
            return self.session.query(self.model_class).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model_class.__name__}: {e}")
            return 0
    
    def exists(self, id: int) -> bool:
        """Check if model instance exists by ID.
        
        Args:
            id: Primary key ID
            
        Returns:
            True if exists, False otherwise
        """
        try:
            return self.session.query(self.model_class).filter(
                self.model_class.id == id
            ).count() > 0
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model_class.__name__} {id}: {e}")
            return False 