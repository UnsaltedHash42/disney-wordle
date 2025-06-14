"""Statistics API blueprint for statistics and leaderboard endpoints."""

import logging
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..services.statistics_service import StatisticsService
from ..models.game import GameMode
from ..utils.responses import success_response, error_response

logger = logging.getLogger(__name__)

# Create blueprint
stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')

# Initialize services
stats_service = StatisticsService()


@stats_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_stats(user_id: int):
    """Get user statistics for all game modes.
    
    Args:
        user_id: User ID to get stats for
        
    Query parameters:
        mode: Specific game mode ('classic' or 'disney') - optional
        
    Returns:
        JSON response with user statistics
    """
    try:
        # Get current user ID from JWT token
        current_user_id = get_jwt_identity()
        requesting_user_id = int(current_user_id)
        
        # Users can only view their own detailed stats, others can view limited stats
        is_own_stats = (requesting_user_id == user_id)
        
        # Get mode parameter
        mode_param = request.args.get('mode')
        
        if mode_param:
            # Get stats for specific mode
            try:
                game_mode = GameMode(mode_param.lower())
            except ValueError:
                return error_response("Invalid game mode. Must be 'classic' or 'disney'", status_code=400)
            
            stats = stats_service.get_user_stats(user_id, game_mode)
            
            # Filter sensitive information for non-own stats
            if not is_own_stats:
                stats = _filter_public_stats(stats)
            
            return success_response(stats)
        else:
            # Get stats for all modes
            all_stats = stats_service.get_user_all_stats(user_id)
            
            # Filter sensitive information for non-own stats
            if not is_own_stats:
                all_stats = _filter_public_all_stats(all_stats)
            
            return success_response(all_stats)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error getting user stats for user {user_id}: {e}")
        return error_response("Internal server error", status_code=500)


@stats_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_stats():
    """Get current user's statistics for all game modes.
    
    Query parameters:
        mode: Specific game mode ('classic' or 'disney') - optional
        
    Returns:
        JSON response with user statistics
    """
    try:
        # Get current user ID from JWT token
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id)
        
        # Get mode parameter
        mode_param = request.args.get('mode')
        
        if mode_param:
            # Get stats for specific mode
            try:
                game_mode = GameMode(mode_param.lower())
            except ValueError:
                return error_response("Invalid game mode. Must be 'classic' or 'disney'", status_code=400)
            
            stats = stats_service.get_user_stats(user_id, game_mode)
            return success_response(stats)
        else:
            # Get stats for all modes
            all_stats = stats_service.get_user_all_stats(user_id)
            return success_response(all_stats)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error getting own stats for user {current_user_id}: {e}")
        return error_response("Internal server error", status_code=500)


@stats_bp.route('/leaderboard/<game_mode>', methods=['GET'])
def get_leaderboard(game_mode: str):
    """Get leaderboard for a specific game mode.
    
    Args:
        game_mode: Game mode ('classic' or 'disney')
        
    Query parameters:
        metric: Ranking metric ('win_percentage', 'total_wins', 'current_streak') - default: 'win_percentage'
        limit: Number of users to return (default: 10, max: 50)
        
    Returns:
        JSON response with leaderboard data
    """
    try:
        # Validate game mode
        try:
            mode = GameMode(game_mode.lower())
        except ValueError:
            return error_response("Invalid game mode. Must be 'classic' or 'disney'", status_code=400)
        
        # Get query parameters
        metric = request.args.get('metric', 'win_percentage').lower()
        limit = request.args.get('limit', 10, type=int)
        
        # Validate metric
        valid_metrics = ['win_percentage', 'total_wins', 'current_streak']
        if metric not in valid_metrics:
            return error_response(f"Invalid metric. Must be one of: {', '.join(valid_metrics)}", status_code=400)
        
        # Validate limit
        if limit > 50:
            limit = 50
        elif limit < 1:
            limit = 1
        
        # Get leaderboard
        leaderboard = stats_service.get_leaderboard(mode, metric, limit)
        
        return success_response({
            'game_mode': mode.value,
            'metric': metric,
            'leaderboard': leaderboard,
            'count': len(leaderboard)
        })
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error getting leaderboard for mode {game_mode}: {e}")
        return error_response("Internal server error", status_code=500)


@stats_bp.route('/global/<game_mode>', methods=['GET'])
def get_global_stats(game_mode: str):
    """Get global statistics for a specific game mode.
    
    Args:
        game_mode: Game mode ('classic' or 'disney')
        
    Returns:
        JSON response with global statistics
    """
    try:
        # Validate game mode
        try:
            mode = GameMode(game_mode.lower())
        except ValueError:
            return error_response("Invalid game mode. Must be 'classic' or 'disney'", status_code=400)
        
        # Get global statistics
        global_stats = stats_service.get_global_statistics(mode)
        
        return success_response(global_stats)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error getting global stats for mode {game_mode}: {e}")
        return error_response("Internal server error", status_code=500)


@stats_bp.route('/rank/<game_mode>', methods=['GET'])
@jwt_required()
def get_user_rank(game_mode: str):
    """Get current user's rank for a specific game mode.
    
    Args:
        game_mode: Game mode ('classic' or 'disney')
        
    Query parameters:
        metric: Ranking metric ('win_percentage', 'total_wins', 'current_streak') - default: 'win_percentage'
        
    Returns:
        JSON response with user's rank information
    """
    try:
        # Validate game mode
        try:
            mode = GameMode(game_mode.lower())
        except ValueError:
            return error_response("Invalid game mode. Must be 'classic' or 'disney'", status_code=400)
        
        # Get current user ID from JWT token
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id)
        
        # Get metric parameter
        metric = request.args.get('metric', 'win_percentage').lower()
        
        # Validate metric
        valid_metrics = ['win_percentage', 'total_wins', 'current_streak']
        if metric not in valid_metrics:
            return error_response(f"Invalid metric. Must be one of: {', '.join(valid_metrics)}", status_code=400)
        
        # Get user rank
        rank_info = stats_service.get_user_rank(user_id, mode, metric)
        
        return success_response(rank_info)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error getting user rank for mode {game_mode}: {e}")
        return error_response("Internal server error", status_code=500)


@stats_bp.route('/streak/<game_mode>', methods=['GET'])
@jwt_required()
def get_streak_analysis(game_mode: str):
    """Get current user's streak analysis for a specific game mode.
    
    Args:
        game_mode: Game mode ('classic' or 'disney')
        
    Returns:
        JSON response with streak analysis
    """
    try:
        # Validate game mode
        try:
            mode = GameMode(game_mode.lower())
        except ValueError:
            return error_response("Invalid game mode. Must be 'classic' or 'disney'", status_code=400)
        
        # Get current user ID from JWT token
        current_user_id = get_jwt_identity()
        user_id = int(current_user_id)
        
        # Get streak analysis
        streak_analysis = stats_service.get_streak_analysis(user_id, mode)
        
        return success_response(streak_analysis)
        
    except ValueError as e:
        return error_response(str(e), status_code=400)
    except Exception as e:
        logger.error(f"Error getting streak analysis for mode {game_mode}: {e}")
        return error_response("Internal server error", status_code=500)


@stats_bp.route('/summary', methods=['GET'])
def get_stats_summary():
    """Get summary of statistics across all game modes.
    
    Returns:
        JSON response with statistics summary
    """
    try:
        summary = {}
        
        for mode in GameMode:
            try:
                global_stats = stats_service.get_global_statistics(mode)
                summary[mode.value] = {
                    'total_players': global_stats.get('total_players', 0),
                    'total_games': global_stats.get('total_games', 0),
                    'global_win_percentage': global_stats.get('global_win_percentage', 0.0)
                }
            except Exception as e:
                logger.warning(f"Error getting summary for mode {mode}: {e}")
                summary[mode.value] = {
                    'total_players': 0,
                    'total_games': 0,
                    'global_win_percentage': 0.0
                }
        
        return success_response({
            'modes': summary,
            'total_modes': len(summary)
        })
        
    except Exception as e:
        logger.error(f"Error getting stats summary: {e}")
        return error_response("Internal server error", status_code=500)


def _filter_public_stats(stats: dict) -> dict:
    """Filter user stats to show only public information.
    
    Args:
        stats: Full user statistics dictionary
        
    Returns:
        Filtered statistics dictionary with only public info
    """
    return {
        'game_mode': stats.get('game_mode'),
        'games_played': stats.get('games_played', 0),
        'games_won': stats.get('games_won', 0),
        'win_percentage': stats.get('win_percentage', 0.0),
        'current_streak': stats.get('current_streak', 0),
        'max_streak': stats.get('max_streak', 0)
        # Exclude: guess_distribution, average_guesses, total_guesses, last_updated
    }


def _filter_public_all_stats(all_stats: dict) -> dict:
    """Filter all user stats to show only public information.
    
    Args:
        all_stats: Full user statistics dictionary for all modes
        
    Returns:
        Filtered statistics dictionary with only public info
    """
    filtered = {
        'user_id': all_stats.get('user_id'),
        'modes': {},
        'overall': all_stats.get('overall', {})
    }
    
    # Filter each mode's stats
    for mode, stats in all_stats.get('modes', {}).items():
        filtered['modes'][mode] = _filter_public_stats(stats)
    
    return filtered