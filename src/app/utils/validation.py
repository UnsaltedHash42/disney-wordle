"""Request validation utilities using Pydantic."""

from functools import wraps
from typing import Type, Callable, Any

from flask import request, jsonify, g
from pydantic import BaseModel, ValidationError

from .responses import error_response


def validate_json(model_class: Type[BaseModel]) -> Callable:
    """Decorator to validate JSON request data using Pydantic model.
    
    Args:
        model_class: Pydantic model class for validation
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Get JSON data from request
                json_data = request.get_json()
                
                if json_data is None:
                    return error_response("Request must contain JSON data", status_code=400)
                
                # Validate data using Pydantic model
                validated_data = model_class(**json_data)
                
                # Store validated data in Flask's g object instead of modifying request
                g.validated_data = validated_data.model_dump()
                
                # Call the original function
                return func(*args, **kwargs)
                
            except ValidationError as e:
                # Extract validation errors
                error_details = {}
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc'])
                    error_details[field] = error['msg']
                
                return error_response(
                    "Validation failed",
                    status_code=400,
                    details=error_details
                )
            
            except Exception as e:
                return error_response("Request must contain valid JSON data", status_code=400)
        
        return wrapper
    return decorator


def validate_query_params(model_class: Type[BaseModel]) -> Callable:
    """Decorator to validate query parameters using Pydantic model.
    
    Args:
        model_class: Pydantic model class for validation
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Get query parameters
                query_data = request.args.to_dict()
                
                # Validate data using Pydantic model
                validated_data = model_class(**query_data)
                
                # Add validated data to kwargs
                kwargs['query_params'] = validated_data
                
                # Call the original function
                return func(*args, **kwargs)
                
            except ValidationError as e:
                # Extract validation errors
                error_details = {}
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc'])
                    error_details[field] = error['msg']
                
                return error_response(
                    "Query parameter validation failed",
                    status_code=400,
                    details=error_details
                )
        
        return wrapper
    return decorator 