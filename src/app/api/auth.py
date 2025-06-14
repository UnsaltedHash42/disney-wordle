"""Authentication API endpoints."""

from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, set_access_cookies, set_refresh_cookies
from pydantic import BaseModel, ValidationError

from ..services.auth_service import AuthService
from ..utils.responses import success_response, error_response
from ..utils.validation import validate_json

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize service
auth_service = AuthService()


class RegisterRequest(BaseModel):
    """Request model for user registration."""
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: str
    password: str


@auth_bp.route('/register', methods=['POST'])
@validate_json(RegisterRequest)
def register():
    """Register a new user.
    
    Returns:
        JSON response with user data and tokens
    """
    try:
        # Get validated data from Flask's g object
        from flask import g
        data = g.validated_data
        
        user = auth_service.register_user(data)
        
        # Create tokens (convert user.id to string for JWT)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # SSR compatibility: set JWTs as HttpOnly cookies
        resp = make_response(success_response({
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }, status_code=201))
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        return resp
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        return error_response("Registration failed", status_code=500)


@auth_bp.route('/login', methods=['POST'])
@validate_json(LoginRequest)
def login():
    """Authenticate user and return tokens.
    
    Returns:
        JSON response with user data and tokens
    """
    try:
        # Get validated data from Flask's g object
        from flask import g
        data = g.validated_data
        
        user = auth_service.authenticate_user(data['email'], data['password'])
        
        # Create tokens (convert user.id to string for JWT)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # SSR compatibility: set JWTs as HttpOnly cookies
        resp = make_response(success_response({
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }))
        set_access_cookies(resp, access_token)
        set_refresh_cookies(resp, refresh_token)
        return resp
        
    except ValueError as e:
        return error_response(str(e), status_code=401)
    except Exception as e:
        return error_response("Authentication failed", status_code=500)


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token.
    
    Returns:
        JSON response with new access token
    """
    try:
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(int(current_user_id))
        
        if not user or not user.is_active:
            return error_response("User not found or inactive", status_code=401)
        
        # Create new access token
        access_token = create_access_token(identity=current_user_id)
        
        return success_response({
            'access_token': access_token
        })
        
    except Exception as e:
        return error_response("Token refresh failed", status_code=401)


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user information.
    
    Returns:
        JSON response with current user data
    """
    try:
        current_user_id = get_jwt_identity()
        user = auth_service.get_user_by_id(int(current_user_id))
        
        if not user:
            return error_response("User not found", status_code=404)
        
        return success_response({
            'user': user.to_dict()
        })
        
    except Exception as e:
        return error_response("Failed to get user information", status_code=500) 