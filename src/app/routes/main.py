"""Main routes for serving frontend templates."""

from flask import Blueprint, render_template, redirect, url_for, request
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

# Create blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page - redirect based on authentication status."""
    try:
        verify_jwt_in_request(optional=True)
        current_user = get_jwt_identity()
        
        if current_user:
            return redirect(url_for('main.game'))
        else:
            return redirect(url_for('main.auth_login'))
    except:
        return redirect(url_for('main.auth_login'))


@main_bp.route('/auth/login')
def auth_login():
    """Login page."""
    # Redirect if already authenticated
    try:
        verify_jwt_in_request(optional=True)
        current_user = get_jwt_identity()
        if current_user:
            return redirect(url_for('main.game'))
    except:
        pass
    
    return render_template('auth/login.html')


@main_bp.route('/auth/register')
def auth_register():
    """Registration page."""
    # Redirect if already authenticated
    try:
        verify_jwt_in_request(optional=True)
        current_user = get_jwt_identity()
        if current_user:
            return redirect(url_for('main.game'))
    except:
        pass
    
    return render_template('auth/register.html')


@main_bp.route('/game')
@jwt_required(optional=True)
def game():
    """Main game page."""
    current_user = get_jwt_identity()
    if not current_user:
        return redirect(url_for('main.auth_login'))
    
    return render_template('game/play.html')


@main_bp.route('/stats')
@jwt_required(optional=True)
def stats():
    """Statistics page."""
    current_user = get_jwt_identity()
    if not current_user:
        return redirect(url_for('main.auth_login'))
    
    return render_template('game/stats.html')


@main_bp.route('/history')
@jwt_required(optional=True)
def history():
    """Game history page."""
    current_user = get_jwt_identity()
    if not current_user:
        return redirect(url_for('main.auth_login'))
    
    return render_template('game/history.html')