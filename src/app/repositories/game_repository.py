"""Game repositories for all game-related models."""

import logging
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, desc

from .base_repository import BaseRepository
from ..models.game import GameMode, WordList, GameSession, UserStats

logger = logging.getLogger(__name__)


class WordListRepository(BaseRepository[WordList]):
    """Repository for WordList model with specific query methods."""
    
    def __init__(self):
        """Initialize word list repository."""
        super().__init__(WordList)
    
    def get_by_word_and_mode(self, word: str, game_mode: GameMode) -> Optional[WordList]:
        """Get word list entry by word and game mode.
        
        Args:
            word: Word to search for
            game_mode: Game mode to search in
            
        Returns:
            WordList entry if found, None otherwise
        """
        try:
            return self.session.query(WordList).filter(
                and_(
                    WordList.word == word.upper(),
                    WordList.game_mode == game_mode
                )
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting word {word} for mode {game_mode}: {e}")
            self.session.rollback()
            return None
    
    def is_valid_word(self, word: str, game_mode: GameMode) -> bool:
        """Check if word is valid for guessing in the given mode.
        
        Args:
            word: Word to validate
            game_mode: Game mode to check against
            
        Returns:
            True if word is valid for guessing, False otherwise
        """
        try:
            return self.session.query(WordList).filter(
                and_(
                    WordList.word == word.upper(),
                    WordList.game_mode == game_mode
                )
            ).count() > 0
        except SQLAlchemyError as e:
            logger.error(f"Error validating word {word} for mode {game_mode}: {e}")
            return False
    
    def is_answer_word(self, word: str, game_mode: GameMode) -> bool:
        """Check if word can be used as an answer in the given mode.
        
        Args:
            word: Word to check
            game_mode: Game mode to check against
            
        Returns:
            True if word can be an answer, False otherwise
        """
        try:
            word_entry = self.session.query(WordList).filter(
                and_(
                    WordList.word == word.upper(),
                    WordList.game_mode == game_mode,
                    WordList.is_answer == True
                )
            ).first()
            return word_entry is not None
        except SQLAlchemyError as e:
            logger.error(f"Error checking answer word {word} for mode {game_mode}: {e}")
            return False
    
    def get_answer_words_by_mode(self, game_mode: GameMode, limit: Optional[int] = None) -> List[WordList]:
        """Get answer words for a game mode, optionally limited.
        
        Args:
            game_mode: Game mode to get words for
            limit: Optional limit on number of words
            
        Returns:
            List of WordList entries that can be answers
        """
        try:
            query = self.session.query(WordList).filter(
                and_(
                    WordList.game_mode == game_mode,
                    WordList.is_answer == True
                )
            ).order_by(WordList.frequency_rank.asc().nullslast())
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting answer words for mode {game_mode}: {e}")
            self.session.rollback()
            return []


class GameSessionRepository(BaseRepository[GameSession]):
    """Repository for GameSession model with specific query methods (unlimited play)."""
    
    def __init__(self):
        """Initialize game session repository."""
        super().__init__(GameSession)
    
    def create_new_session(self, user_id: int, answer_word: str, game_mode: GameMode) -> GameSession:
        """Create a new game session for a user with a random answer word."""
        new_session = GameSession(
            user_id=user_id,
            answer_word=answer_word,
            game_mode=game_mode,
            guesses=[],
            completed=False,
            won=False,
            attempts_used=0
        )
        return self.create(new_session)
    
    def get_user_sessions_by_mode(self, user_id: int, game_mode: GameMode, limit: int = 10) -> List[GameSession]:
        """Get user's game sessions for a specific mode."""
        try:
            query = self.session.query(GameSession).filter(
                GameSession.user_id == user_id,
                GameSession.game_mode == game_mode
            ).order_by(GameSession.created_at.desc())
            if limit:
                query = query.limit(limit)
            return query.all()
        except Exception as e:
            logger.error(f"Error getting user sessions for user {user_id}, mode {game_mode}: {e}")
            self.session.rollback()
            return []


class UserStatsRepository(BaseRepository[UserStats]):
    """Repository for UserStats model with specific query methods."""
    
    def __init__(self):
        """Initialize user stats repository."""
        super().__init__(UserStats)
    
    def get_by_user_and_mode(self, user_id: int, game_mode: GameMode) -> Optional[UserStats]:
        """Get user stats by user ID and game mode.
        
        Args:
            user_id: User ID
            game_mode: Game mode
            
        Returns:
            UserStats if found, None otherwise
        """
        try:
            return self.session.query(UserStats).filter(
                and_(
                    UserStats.user_id == user_id,
                    UserStats.game_mode == game_mode
                )
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user stats for user {user_id}, mode {game_mode}: {e}")
            self.session.rollback()
            return None
    
    def get_leaderboard_by_wins(self, game_mode: GameMode, limit: int = 10) -> List[UserStats]:
        """Get leaderboard by total wins for a game mode.
        
        Args:
            game_mode: Game mode to get leaderboard for
            limit: Number of top users to return
            
        Returns:
            List of UserStats ordered by games won (descending)
        """
        try:
            return self.session.query(UserStats).filter(
                UserStats.game_mode == game_mode
            ).order_by(desc(UserStats.games_won)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting wins leaderboard for mode {game_mode}: {e}")
            self.session.rollback()
            return []
    
    def get_leaderboard_by_streak(self, game_mode: GameMode, limit: int = 10) -> List[UserStats]:
        """Get leaderboard by current streak for a game mode.
        
        Args:
            game_mode: Game mode to get leaderboard for
            limit: Number of top users to return
            
        Returns:
            List of UserStats ordered by current streak (descending)
        """
        try:
            return self.session.query(UserStats).filter(
                UserStats.game_mode == game_mode
            ).order_by(desc(UserStats.current_streak)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting streak leaderboard for mode {game_mode}: {e}")
            self.session.rollback()
            return []
    
    def get_leaderboard_by_win_percentage(self, game_mode: GameMode, min_games: int = 5, limit: int = 10) -> List[UserStats]:
        """Get leaderboard by win percentage for a game mode.
        
        Args:
            game_mode: Game mode to get leaderboard for
            min_games: Minimum games played to qualify
            limit: Number of top users to return
            
        Returns:
            List of UserStats ordered by win percentage (descending)
        """
        try:
            # Calculate win percentage and order by it
            return self.session.query(UserStats).filter(
                and_(
                    UserStats.game_mode == game_mode,
                    UserStats.games_played >= min_games
                )
            ).order_by(
                desc(UserStats.games_won * 100.0 / UserStats.games_played)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting win percentage leaderboard for mode {game_mode}: {e}")
            self.session.rollback()
            return []
    
    def stats_exist(self, user_id: int, game_mode: GameMode) -> bool:
        """Check if stats exist for user and game mode.
        
        Args:
            user_id: User ID
            game_mode: Game mode
            
        Returns:
            True if stats exist, False otherwise
        """
        try:
            return self.session.query(UserStats).filter(
                and_(
                    UserStats.user_id == user_id,
                    UserStats.game_mode == game_mode
                )
            ).count() > 0
        except SQLAlchemyError as e:
            logger.error(f"Error checking stats existence for user {user_id}, mode {game_mode}: {e}")
            return False 