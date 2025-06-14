"""Game service orchestrating all game logic."""

import logging
from datetime import date
from typing import Optional, Dict, Any, List

from ..models.game import GameMode, DailyWord, GameSession, UserStats
from ..repositories.game_repository import DailyWordRepository, GameSessionRepository, UserStatsRepository
from .daily_puzzle_service import DailyPuzzleService
from .guess_processing_service import GuessProcessingService
from .word_validation_service import WordValidationService

logger = logging.getLogger(__name__)


class GameService:
    """Main service orchestrating all game logic."""
    
    def __init__(self):
        """Initialize game service with all dependencies."""
        self.daily_word_repo = DailyWordRepository()
        self.session_repo = GameSessionRepository()
        self.stats_repo = UserStatsRepository()
        
        self.daily_puzzle_service = DailyPuzzleService()
        self.guess_processor = GuessProcessingService()
        self.word_validator = WordValidationService()
    
    def get_daily_puzzle(self, user_id: int, game_mode: GameMode, puzzle_date: Optional[date] = None) -> Dict[str, Any]:
        """Get or create daily puzzle and user session.
        
        Args:
            user_id: User ID
            game_mode: Game mode (classic or disney)
            puzzle_date: Specific date (defaults to today)
            
        Returns:
            Dictionary with puzzle and session information
        """
        try:
            # Use today if no date specified
            if puzzle_date is None:
                puzzle_date = self.daily_puzzle_service.get_current_date()
            
            # Ensure daily word exists
            daily_word = self.daily_puzzle_service.ensure_today_puzzle_exists(game_mode)
            if not daily_word:
                return {
                    'success': False,
                    'error': 'Failed to create or retrieve daily puzzle'
                }
            
            # Get or create user session
            session = self._get_or_create_session(user_id, daily_word.id)
            if not session:
                return {
                    'success': False,
                    'error': 'Failed to create game session'
                }
            
            # Get puzzle info
            puzzle_info = self.daily_puzzle_service.get_puzzle_info(puzzle_date, game_mode)
            
            # Build response
            return {
                'success': True,
                'puzzle': {
                    'id': daily_word.id,
                    'date': daily_word.date.isoformat(),
                    'game_mode': daily_word.game_mode.value,
                    'puzzle_number': puzzle_info.get('puzzle_number', 1)
                },
                'session': {
                    'id': session.id,
                    'guesses': session.guesses or [],
                    'completed': session.completed,
                    'won': session.won,
                    'attempts_used': session.attempts_used,
                    'max_attempts': 6
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting daily puzzle for user {user_id}, mode {game_mode}: {e}")
            return {
                'success': False,
                'error': 'Internal server error'
            }
    
    def process_guess(self, user_id: int, guess_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a user's guess and update game state.
        
        Args:
            user_id: User ID
            guess_data: Dictionary containing guess information
                - word: The guessed word
                - session_id: Game session ID
                
        Returns:
            Dictionary with guess result and updated game state
        """
        try:
            # Validate input
            word = guess_data.get('word', '').strip().upper()
            session_id = guess_data.get('session_id')
            
            if not word or not session_id:
                return {
                    'success': False,
                    'error': 'Word and session_id are required'
                }
            
            # Get game session
            session = self.session_repo.get_by_id(session_id)
            if not session or session.user_id != user_id:
                return {
                    'success': False,
                    'error': 'Invalid session'
                }
            
            # Check if game is already over
            if session.is_game_over():
                return {
                    'success': False,
                    'error': 'Game is already completed'
                }
            
            # Get daily word
            daily_word = self.daily_word_repo.get_by_id(session.daily_word_id)
            if not daily_word:
                return {
                    'success': False,
                    'error': 'Daily word not found'
                }
            
            # Validate word format
            is_valid_format, format_error = self.word_validator.validate_word_format(word)
            if not is_valid_format:
                return {
                    'success': False,
                    'error': format_error
                }
            
            # Validate word exists in word list
            if not self.word_validator.is_valid_guess(word, daily_word.game_mode):
                return {
                    'success': False,
                    'error': 'Word not in word list'
                }
            
            # Process the guess
            feedback = self.guess_processor.process_guess(word, daily_word.word)
            is_correct = self.guess_processor.is_winning_guess(feedback)
            
            # Update session
            session.add_guess(word, feedback)
            
            # Check if game is complete
            if is_correct or session.get_current_guess_count() >= 6:
                session.completed = True
                session.won = is_correct
                
                # Update user statistics
                self._update_user_stats(user_id, daily_word.game_mode, session.won, session.attempts_used)
            
            # Save session
            updated_session = self.session_repo.update(session.id, {
                'guesses': session.guesses,
                'completed': session.completed,
                'won': session.won,
                'attempts_used': session.attempts_used
            })
            
            if not updated_session:
                return {
                    'success': False,
                    'error': 'Failed to update session'
                }
            
            # Prepare response
            result = {
                'success': True,
                'guess': {
                    'word': word,
                    'feedback': feedback,
                    'is_correct': is_correct
                },
                'session': {
                    'id': session.id,
                    'guesses': session.guesses,
                    'completed': session.completed,
                    'won': session.won,
                    'attempts_used': session.attempts_used,
                    'attempts_remaining': 6 - session.attempts_used
                }
            }
            
            # Add target word if game is complete
            if session.completed:
                result['target_word'] = daily_word.word
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing guess for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Internal server error'
            }
    
    def get_game_session(self, user_id: int, session_id: int) -> Dict[str, Any]:
        """Get game session details.
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Dictionary with session information
        """
        try:
            session = self.session_repo.get_by_id(session_id)
            if not session or session.user_id != user_id:
                return {
                    'success': False,
                    'error': 'Session not found'
                }
            
            # Get daily word
            daily_word = self.daily_word_repo.get_by_id(session.daily_word_id)
            
            return {
                'success': True,
                'session': {
                    'id': session.id,
                    'guesses': session.guesses or [],
                    'completed': session.completed,
                    'won': session.won,
                    'attempts_used': session.attempts_used,
                    'daily_word': {
                        'date': daily_word.date.isoformat() if daily_word else None,
                        'game_mode': daily_word.game_mode.value if daily_word else None,
                        'word': daily_word.word if (daily_word and session.completed) else None
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting session {session_id} for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'Internal server error'
            }
    
    def validate_word(self, word: str, game_mode: GameMode) -> Dict[str, Any]:
        """Validate if a word can be used as a guess.
        
        Args:
            word: Word to validate
            game_mode: Game mode to validate against
            
        Returns:
            Dictionary with validation result
        """
        try:
            # Check format
            is_valid_format, format_error = self.word_validator.validate_word_format(word)
            if not is_valid_format:
                return {
                    'valid': False,
                    'error': format_error
                }
            
            # Check if word exists in word list
            is_valid_guess = self.word_validator.is_valid_guess(word, game_mode)
            
            return {
                'valid': is_valid_guess,
                'word': word.upper(),
                'error': None if is_valid_guess else 'Word not in word list'
            }
            
        except Exception as e:
            logger.error(f"Error validating word {word} for mode {game_mode}: {e}")
            return {
                'valid': False,
                'error': 'Validation error'
            }
    
    def get_user_game_history(self, user_id: int, game_mode: GameMode, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's game history for a specific mode.
        
        Args:
            user_id: User ID
            game_mode: Game mode to get history for
            limit: Maximum number of games to return
            
        Returns:
            List of game session summaries
        """
        try:
            sessions = self.session_repo.get_user_sessions_by_mode(user_id, game_mode, limit)
            
            history = []
            for session in sessions:
                daily_word = self.daily_word_repo.get_by_id(session.daily_word_id)
                
                session_data = {
                    'session_id': session.id,
                    'date': daily_word.date.isoformat() if daily_word else None,
                    'completed': session.completed,
                    'won': session.won,
                    'attempts_used': session.attempts_used,
                    'target_word': daily_word.word if (daily_word and session.completed) else None
                }
                
                history.append(session_data)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting game history for user {user_id}, mode {game_mode}: {e}")
            return []
    
    def _get_or_create_session(self, user_id: int, daily_word_id: int) -> Optional[GameSession]:
        """Get existing session or create new one.
        
        Args:
            user_id: User ID
            daily_word_id: Daily word ID
            
        Returns:
            GameSession if successful, None otherwise
        """
        try:
            # Try to get existing session
            existing_session = self.session_repo.get_by_user_and_daily_word(user_id, daily_word_id)
            if existing_session:
                return existing_session
            
            # Create new session
            new_session = GameSession(
                user_id=user_id,
                daily_word_id=daily_word_id,
                guesses=[],
                completed=False,
                won=False,
                attempts_used=0
            )
            
            return self.session_repo.create(new_session)
            
        except Exception as e:
            logger.error(f"Error getting/creating session for user {user_id}, daily_word {daily_word_id}: {e}")
            return None
    
    def _update_user_stats(self, user_id: int, game_mode: GameMode, won: bool, attempts_used: int) -> None:
        """Update user statistics after game completion.
        
        Args:
            user_id: User ID
            game_mode: Game mode
            won: Whether the game was won
            attempts_used: Number of attempts used
        """
        try:
            # Get or create user stats
            stats = self.stats_repo.get_by_user_and_mode(user_id, game_mode)
            if not stats:
                stats = UserStats(
                    user_id=user_id,
                    game_mode=game_mode,
                    games_played=0,
                    games_won=0,
                    current_streak=0,
                    max_streak=0,
                    guess_distribution={"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}
                )
                stats = self.stats_repo.create(stats)
            
            if stats:
                # Update stats
                stats.update_stats(won, attempts_used)
                
                # Save updated stats
                self.stats_repo.update(stats.id, {
                    'games_played': stats.games_played,
                    'games_won': stats.games_won,
                    'current_streak': stats.current_streak,
                    'max_streak': stats.max_streak,
                    'guess_distribution': stats.guess_distribution
                })
                
                logger.info(f"Updated stats for user {user_id}, mode {game_mode}: {stats.games_played} played, {stats.games_won} won")
            
        except Exception as e:
            logger.error(f"Error updating user stats for user {user_id}, mode {game_mode}: {e}")