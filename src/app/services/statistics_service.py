"""Statistics service for tracking and calculating game statistics."""

import logging
from typing import Dict, Any, List, Optional

from ..models.game import GameMode, UserStats
from ..repositories.game_repository import UserStatsRepository, GameSessionRepository
from ..repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class StatisticsService:
    """Service for managing user statistics and leaderboards."""
    
    def __init__(self):
        """Initialize statistics service."""
        self.stats_repo = UserStatsRepository()
        self.session_repo = GameSessionRepository()
        self.user_repo = UserRepository()
    
    def get_user_stats(self, user_id: int, game_mode: GameMode) -> Dict[str, Any]:
        """Get comprehensive statistics for a user in a specific game mode.
        
        Args:
            user_id: User ID
            game_mode: Game mode to get stats for
            
        Returns:
            Dictionary with user statistics
        """
        try:
            stats = self.stats_repo.get_by_user_and_mode(user_id, game_mode)
            
            if not stats:
                # Return default stats if none exist
                return self._get_default_stats(game_mode)
            
            # Calculate additional metrics
            win_percentage = stats.get_win_percentage()
            average_guesses = stats.get_average_guesses()
            
            return {
                'user_id': user_id,
                'game_mode': game_mode.value,
                'games_played': stats.games_played,
                'games_won': stats.games_won,
                'win_percentage': win_percentage,
                'current_streak': stats.current_streak,
                'max_streak': stats.max_streak,
                'average_guesses': average_guesses,
                'guess_distribution': stats.guess_distribution,
                'total_guesses': self._calculate_total_guesses(stats.guess_distribution),
                'last_updated': stats.updated_at.isoformat() if stats.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats for user {user_id}, mode {game_mode}: {e}")
            return self._get_default_stats(game_mode)
    
    def get_user_all_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics for a user across all game modes.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with stats for all game modes
        """
        try:
            stats = {}
            
            for mode in GameMode:
                stats[mode.value] = self.get_user_stats(user_id, mode)
            
            # Calculate combined stats
            total_games = sum(s['games_played'] for s in stats.values())
            total_wins = sum(s['games_won'] for s in stats.values())
            overall_win_percentage = (total_wins / total_games * 100) if total_games > 0 else 0.0
            
            return {
                'user_id': user_id,
                'modes': stats,
                'overall': {
                    'total_games_played': total_games,
                    'total_games_won': total_wins,
                    'overall_win_percentage': round(overall_win_percentage, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting all stats for user {user_id}: {e}")
            return {
                'user_id': user_id,
                'modes': {},
                'overall': {
                    'total_games_played': 0,
                    'total_games_won': 0,
                    'overall_win_percentage': 0.0
                }
            }
    
    def get_leaderboard(self, game_mode: GameMode, metric: str = 'win_percentage', limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard for a specific game mode and metric.
        
        Args:
            game_mode: Game mode to get leaderboard for
            metric: Metric to rank by ('win_percentage', 'total_wins', 'current_streak')
            limit: Number of top users to return
            
        Returns:
            List of user statistics ordered by the specified metric
        """
        try:
            if metric == 'win_percentage':
                stats_list = self.stats_repo.get_leaderboard_by_win_percentage(game_mode, min_games=5, limit=limit)
            elif metric == 'total_wins':
                stats_list = self.stats_repo.get_leaderboard_by_wins(game_mode, limit=limit)
            elif metric == 'current_streak':
                stats_list = self.stats_repo.get_leaderboard_by_streak(game_mode, limit=limit)
            else:
                logger.warning(f"Unknown leaderboard metric: {metric}")
                return []
            
            leaderboard = []
            for rank, stats in enumerate(stats_list, 1):
                # Get user info
                user = self.user_repo.get_by_id(stats.user_id)
                
                entry = {
                    'rank': rank,
                    'user_id': stats.user_id,
                    'username': user.username if user else 'Unknown',
                    'games_played': stats.games_played,
                    'games_won': stats.games_won,
                    'win_percentage': stats.get_win_percentage(),
                    'current_streak': stats.current_streak,
                    'max_streak': stats.max_streak,
                    'average_guesses': stats.get_average_guesses()
                }
                
                leaderboard.append(entry)
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard for mode {game_mode}, metric {metric}: {e}")
            return []
    
    def get_global_statistics(self, game_mode: GameMode) -> Dict[str, Any]:
        """Get global statistics for a game mode.
        
        Args:
            game_mode: Game mode to get global stats for
            
        Returns:
            Dictionary with global statistics
        """
        try:
            # This would require aggregate queries in the repository
            # For now, we'll implement a basic version
            
            # Get all stats for the mode (this is not efficient for large datasets)
            all_stats = self.stats_repo.session.query(UserStats).filter(
                UserStats.game_mode == game_mode
            ).all()
            
            if not all_stats:
                return {
                    'game_mode': game_mode.value,
                    'total_players': 0,
                    'total_games': 0,
                    'total_wins': 0,
                    'global_win_percentage': 0.0,
                    'average_attempts': 0.0,
                    'guess_distribution_percentage': {str(i): 0.0 for i in range(1, 7)}
                }
            
            # Calculate aggregates
            total_players = len(all_stats)
            total_games = sum(s.games_played for s in all_stats)
            total_wins = sum(s.games_won for s in all_stats)
            global_win_percentage = (total_wins / total_games * 100) if total_games > 0 else 0.0
            
            # Calculate global guess distribution
            global_distribution = {str(i): 0 for i in range(1, 7)}
            total_won_games = 0
            
            for stats in all_stats:
                for attempts, count in stats.guess_distribution.items():
                    if attempts in global_distribution:
                        global_distribution[attempts] += count
                        total_won_games += count
            
            # Convert to percentages
            distribution_percentage = {}
            for attempts, count in global_distribution.items():
                distribution_percentage[attempts] = (count / total_won_games * 100) if total_won_games > 0 else 0.0
            
            # Calculate average attempts for won games
            total_attempts = sum(int(attempts) * count for attempts, count in global_distribution.items())
            average_attempts = total_attempts / total_won_games if total_won_games > 0 else 0.0
            
            return {
                'game_mode': game_mode.value,
                'total_players': total_players,
                'total_games': total_games,
                'total_wins': total_wins,
                'global_win_percentage': round(global_win_percentage, 1),
                'average_attempts': round(average_attempts, 2),
                'guess_distribution_percentage': {k: round(v, 1) for k, v in distribution_percentage.items()}
            }
            
        except Exception as e:
            logger.error(f"Error getting global statistics for mode {game_mode}: {e}")
            return {
                'game_mode': game_mode.value,
                'error': 'Failed to calculate global statistics'
            }
    
    def get_user_rank(self, user_id: int, game_mode: GameMode, metric: str = 'win_percentage') -> Dict[str, Any]:
        """Get user's rank in a specific metric for a game mode.
        
        Args:
            user_id: User ID
            game_mode: Game mode
            metric: Metric to rank by
            
        Returns:
            Dictionary with user's rank information
        """
        try:
            # Get user's stats
            user_stats = self.stats_repo.get_by_user_and_mode(user_id, game_mode)
            if not user_stats:
                return {
                    'user_id': user_id,
                    'game_mode': game_mode.value,
                    'metric': metric,
                    'rank': None,
                    'total_players': 0,
                    'percentile': 0.0
                }
            
            # Get leaderboard to find user's rank
            leaderboard = self.get_leaderboard(game_mode, metric, limit=1000)  # Get more entries
            
            user_rank = None
            for entry in leaderboard:
                if entry['user_id'] == user_id:
                    user_rank = entry['rank']
                    break
            
            total_players = len(leaderboard)
            percentile = ((total_players - user_rank + 1) / total_players * 100) if user_rank else 0.0
            
            return {
                'user_id': user_id,
                'game_mode': game_mode.value,
                'metric': metric,
                'rank': user_rank,
                'total_players': total_players,
                'percentile': round(percentile, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting user rank for user {user_id}, mode {game_mode}, metric {metric}: {e}")
            return {
                'user_id': user_id,
                'game_mode': game_mode.value,
                'metric': metric,
                'error': 'Failed to calculate rank'
            }
    
    def get_streak_analysis(self, user_id: int, game_mode: GameMode) -> Dict[str, Any]:
        """Get detailed streak analysis for a user.
        
        Args:
            user_id: User ID
            game_mode: Game mode
            
        Returns:
            Dictionary with streak analysis
        """
        try:
            # Get user sessions to analyze streak history
            sessions = self.session_repo.get_user_sessions_by_mode(user_id, game_mode, limit=50)
            
            if not sessions:
                return {
                    'user_id': user_id,
                    'game_mode': game_mode.value,
                    'current_streak': 0,
                    'max_streak': 0,
                    'streak_history': [],
                    'last_game_won': False
                }
            
            # Analyze streak patterns
            streak_history = []
            current_streak = 0
            max_streak = 0
            temp_streak = 0
            
            # Sort sessions by date (most recent first)
            sorted_sessions = sorted(sessions, key=lambda x: x.created_at, reverse=True)
            
            for session in sorted_sessions:
                if session.completed:
                    if session.won:
                        temp_streak += 1
                        max_streak = max(max_streak, temp_streak)
                    else:
                        if temp_streak > 0:
                            streak_history.append(temp_streak)
                        temp_streak = 0
            
            # Current streak is the active streak if the last game was won
            if sorted_sessions and sorted_sessions[0].won:
                current_streak = temp_streak
            
            return {
                'user_id': user_id,
                'game_mode': game_mode.value,
                'current_streak': current_streak,
                'max_streak': max_streak,
                'streak_history': streak_history[:10],  # Last 10 streaks
                'last_game_won': sorted_sessions[0].won if sorted_sessions else False,
                'total_completed_games': len([s for s in sessions if s.completed])
            }
            
        except Exception as e:
            logger.error(f"Error getting streak analysis for user {user_id}, mode {game_mode}: {e}")
            return {
                'user_id': user_id,
                'game_mode': game_mode.value,
                'error': 'Failed to analyze streaks'
            }
    
    def _get_default_stats(self, game_mode: GameMode) -> Dict[str, Any]:
        """Get default statistics structure for a user with no games.
        
        Args:
            game_mode: Game mode
            
        Returns:
            Dictionary with default statistics
        """
        return {
            'user_id': None,
            'game_mode': game_mode.value,
            'games_played': 0,
            'games_won': 0,
            'win_percentage': 0.0,
            'current_streak': 0,
            'max_streak': 0,
            'average_guesses': 0.0,
            'guess_distribution': {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0},
            'total_guesses': 0,
            'last_updated': None
        }
    
    def _calculate_total_guesses(self, guess_distribution: Dict[str, int]) -> int:
        """Calculate total number of guesses from distribution.
        
        Args:
            guess_distribution: Dictionary mapping attempt number to count
            
        Returns:
            Total number of guesses made
        """
        try:
            return sum(int(attempts) * count for attempts, count in guess_distribution.items())
        except (ValueError, TypeError):
            return 0