"""Game API blueprint for game-related endpoints."""

import logging
from datetime import date, datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..services.game_service import GameService
from ..services.word_validation_service import WordValidationService
from ..models.game import GameMode
from ..utils.responses import success_response, error_response
from ..utils.validation import validate_json

logger = logging.getLogger(__name__)

# Create blueprint
game_bp = Blueprint('game', __name__, url_prefix='/api/game')

# Initialize services
game_service = GameService()
word_validation_service = WordValidationService()


@game_bp.route('/daily/<game_mode>', methods=['GET'])
@jwt_required()
def get_daily_puzzle(game_mode: str):
    """Get today's daily puzzle for the specified game mode.
    
    Args:
        game_mode: Game mode ('classic' or 'disney')
        
    Returns:
        JSON response with puzzle and session information
    """
    try:
        # Validate game mode
        try:
            mode = GameMode(game_mode.lower())
        except ValueError:
            return error_response("Invalid game mode. Must be 'classic' or 'disney'", status_code=400)
        
        # Get user ID from JWT token
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id)
        
        # Get optional date parameter
        date_str = request.args.get('date')
        puzzle_date = None
        
        if date_str:
            try:
                puzzle_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return error_response("Invalid date format. Use YYYY-MM-DD", status_code=400)
        
        # Get daily puzzle
        result = game_service.get_daily_puzzle(user_id, mode, puzzle_date)
        
        if result['success']:
            return success_response(result)
        else:
            return error_response(result.get('error', 'Failed to get daily puzzle'), status_code=500)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error getting daily puzzle for mode {game_mode}: {e}")
        return error_response("Internal server error", status_code=500)


@game_bp.route('/guess', methods=['POST'])
@jwt_required()
def submit_guess():
    """Submit a guess for the current game session.
    
    Expected JSON body:
        {
            "word": "HELLO",
            "session_id": 123
        }
        
    Returns:
        JSON response with guess result and updated game state
    """
    try:
        # Get user ID from JWT token
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id)
        
        # Get JSON data
        data = request.get_json()
        if not data:
            return error_response("Request must contain JSON data", status_code=400)
        
        # Validate required fields
        if 'word' not in data or 'session_id' not in data:
            return error_response("Missing required fields: word, session_id", status_code=400)
        
        # Process the guess
        result = game_service.process_guess(user_id, data)
        
        if result['success']:
            return success_response(result)
        else:
            status_code = 400 if 'not in word list' in result.get('error', '').lower() else 500
            return error_response(result.get('error', 'Failed to process guess'), status_code=status_code)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error processing guess: {e}")
        return error_response("Internal server error", status_code=500)


@game_bp.route('/session/<int:session_id>', methods=['GET'])
@jwt_required()
def get_game_session(session_id: int):
    """Get game session details.
    
    Args:
        session_id: Game session ID
        
    Returns:
        JSON response with session information
    """
    try:
        # Get user ID from JWT token
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id)
        
        # Get session details
        result = game_service.get_game_session(user_id, session_id)
        
        if result['success']:
            return success_response(result['session'])
        else:
            status_code = 404 if 'not found' in result.get('error', '').lower() else 500
            return error_response(result.get('error', 'Failed to get session'), status_code=status_code)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        return error_response("Internal server error", status_code=500)


@game_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_word():
    """Validate if a word can be used as a guess.
    
    Expected JSON body:
        {
            "word": "HELLO",
            "game_mode": "classic"
        }
        
    Returns:
        JSON response with validation result
    """
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return error_response("Request must contain JSON data", status_code=400)
        
        # Validate required fields
        if 'word' not in data or 'game_mode' not in data:
            return error_response("Missing required fields: word, game_mode", status_code=400)
        
        word = data['word'].strip()
        game_mode_str = data['game_mode'].strip().lower()
        
        # Validate game mode
        try:
            game_mode = GameMode(game_mode_str)
        except ValueError:
            return error_response("Invalid game mode. Must be 'classic' or 'disney'", status_code=400)
        
        # Validate word
        result = game_service.validate_word(word, game_mode)
        
        return success_response(result)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error validating word: {e}")
        return error_response("Internal server error", status_code=500)


@game_bp.route('/history/<game_mode>', methods=['GET'])
@jwt_required()
def get_game_history(game_mode: str):
    """Get user's game history for a specific mode.
    
    Args:
        game_mode: Game mode ('classic' or 'disney')
        
    Query parameters:
        limit: Maximum number of games to return (default: 10, max: 50)
        
    Returns:
        JSON response with game history
    """
    try:
        # Validate game mode
        try:
            mode = GameMode(game_mode.lower())
        except ValueError:
            return error_response("Invalid game mode. Must be 'classic' or 'disney'", status_code=400)
        
        # Get user ID from JWT token
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id)
        
        # Get limit parameter
        limit = request.args.get('limit', 10, type=int)
        if limit > 50:
            limit = 50
        elif limit < 1:
            limit = 1
        
        # Get game history
        history = game_service.get_user_game_history(user_id, mode, limit)
        
        return success_response({
            'game_mode': mode.value,
            'history': history,
            'count': len(history)
        })
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error getting game history for mode {game_mode}: {e}")
        return error_response("Internal server error", status_code=500)


@game_bp.route('/modes', methods=['GET'])
def get_game_modes():
    """Get available game modes.
    
    Returns:
        JSON response with available game modes
    """
    try:
        modes = [
            {
                'value': GameMode.CLASSIC.value,
                'name': 'Classic Wordle',
                'description': 'Traditional 5-letter word game with ~2,300 words'
            },
            {
                'value': GameMode.DISNEY.value,
                'name': 'Disney Wordle',
                'description': 'Disney-themed words including characters, movies, and concepts'
            }
        ]
        
        return success_response({
            'modes': modes,
            'count': len(modes)
        })
        
    except Exception as e:
        logger.error(f"Error getting game modes: {e}")
        return error_response("Internal server error", status_code=500)


@game_bp.route('/status/<game_mode>', methods=['GET'])
@jwt_required()
def get_game_status(game_mode: str):
    """Get current game status for a user in a specific mode.
    
    Args:
        game_mode: Game mode ('classic' or 'disney')
        
    Returns:
        JSON response with current game status
    """
    try:
        # Validate game mode
        try:
            mode = GameMode(game_mode.lower())
        except ValueError:
            return error_response("Invalid game mode. Must be 'classic' or 'disney'", status_code=400)
        
        # Get user ID from JWT token
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id)
        
        # Get today's puzzle info
        result = game_service.get_daily_puzzle(user_id, mode)
        
        if result['success']:
            session = result['session']
            puzzle = result['puzzle']
            
            status = {
                'has_todays_puzzle': True,
                'puzzle_date': puzzle['date'],
                'puzzle_number': puzzle['puzzle_number'],
                'session_active': not session['completed'],
                'game_completed': session['completed'],
                'game_won': session['won'],
                'attempts_used': session['attempts_used'],
                'attempts_remaining': session['max_attempts'] - session['attempts_used']
            }
        else:
            status = {
                'has_todays_puzzle': False,
                'error': result.get('error')
            }
        
        return success_response(status)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error getting game status for mode {game_mode}: {e}")
        return error_response("Internal server error", status_code=500)