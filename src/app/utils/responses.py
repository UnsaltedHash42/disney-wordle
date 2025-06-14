"""Standard response utilities for API endpoints."""

from typing import Any, Optional, Dict
from flask import jsonify


def success_response(data: Any = None, status_code: int = 200) -> tuple:
    """Create standardized success response.
    
    Args:
        data: Response data to include
        status_code: HTTP status code
        
    Returns:
        Tuple of (JSON response, status code)
    """
    response = {
        'success': True,
        'data': data,
        'error': None
    }
    return jsonify(response), status_code


def error_response(message: str, status_code: int = 400, details: Optional[Dict] = None) -> tuple:
    """Create standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        Tuple of (JSON response, status code)
    """
    response = {
        'success': False,
        'data': None,
        'error': message
    }
    
    if details:
        response['details'] = details
    
    return jsonify(response), status_code


def paginated_response(items: list, page: int, per_page: int, total: int) -> Dict[str, Any]:
    """Create paginated response data.
    
    Args:
        items: List of items for current page
        page: Current page number
        per_page: Items per page
        total: Total number of items
        
    Returns:
        Paginated response data structure
    """
    total_pages = (total + per_page - 1) // per_page
    
    return {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    } 