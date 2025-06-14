"""Game repositories for all game-related models."""

import logging
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, desc

from .base_repository import BaseRepository
from ..models.game import GameMode, DailyWord, WordList, GameSession, UserStats

logger = logging.getLogger(__name__)


class DailyWordRepository(BaseRepository[DailyWord]):
    """Repository for DailyWord model with specific query methods."""
    
    def __init__(self):
        """Initialize daily word repository."""
        super().__init__(DailyWord)
    
    def get_by_date_and_mode(self, puzzle_date: date, game_mode: GameMode) -> Optional[DailyWord]:
        """Get daily word by date and game mode.
        
        Args:
            puzzle_date: Date of the puzzle
            game_mode: Game mode (classic or disney)
            
        Returns:
            DailyWord if found, None otherwise
        """
        try:
            return self.session.query(DailyWord).filter(
                and_(
                    DailyWord.date == puzzle_date,
                    DailyWord.game_mode == game_mode
                )
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting daily word for {puzzle_date} {game_mode}: {e}")
            self.session.rollback()
            return None
    
    def get_latest_by_mode(self, game_mode: GameMode) -> Optional[DailyWord]:
        """Get latest daily word for a game mode.
        
        Args:
            game_mode: Game mode to query
            
        Returns:
            Latest DailyWord for the mode, None if not found
        """
        try:
            return self.session.query(DailyWord).filter(
                DailyWord.game_mode == game_mode
            ).order_by(desc(DailyWord.date)).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest daily word for {game_mode}: {e}")
            self.session.rollback()
            return None
    
    def exists_for_date_and_mode(self, puzzle_date: date, game_mode: GameMode) -> bool:
        """Check if daily word exists for date and mode.
        
        Args:
            puzzle_date: Date to check
            game_mode: Game mode to check
            
        Returns:
            True if daily word exists, False otherwise
        """
        try:
            return self.session.query(DailyWord).filter(
                and_(
                    DailyWord.date == puzzle_date,
                    DailyWord.game_mode == game_mode
                )
            ).count() > 0
        except SQLAlchemyError as e:
            logger.error(f"Error checking daily word existence for {puzzle_date} {game_mode}: {e}")
            return False


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
    """Repository for GameSession model with specific query methods."""
    
    def __init__(self):
        """Initialize game session repository."""
        super().__init__(GameSession)
    
    def get_by_user_and_daily_word(self, user_id: int, daily_word_id: int) -> Optional[GameSession]:
        """Get game session by user and daily word.
        
        Args:
            user_id: User ID
            daily_word_id: Daily word ID
            
        Returns:
            GameSession if found, None otherwise
        """
        try:
            return self.session.query(GameSession).filter(
                and_(
                    GameSession.user_id == user_id,
                    GameSession.daily_word_id == daily_word_id
                )
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting game session for user {user_id}, daily_word {daily_word_id}: {e}")
            self.session.rollback()
            return None
    
    def get_user_sessions_by_mode(self, user_id: int, game_mode: GameMode, limit: Optional[int] = None) -> List[GameSession]:
        """Get user's game sessions for a specific mode.
        
        Args:
            user_id: User ID
            game_mode: Game mode to filter by
            limit: Optional limit on number of sessions
            
        Returns:
            List of GameSession objects
        """
        try:
            query = self.session.query(GameSession).join(DailyWord).filter(
                and_(
                    GameSession.user_id == user_id,
                    DailyWord.game_mode == game_mode
                )
            ).order_by(desc(DailyWord.date))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting user sessions for user {user_id}, mode {game_mode}: {e}")
            self.session.rollback()
            return []
    
    def get_completed_sessions_count(self, user_id: int, game_mode: GameMode) -> int:
        """Get count of completed sessions for user in a mode.
        
        Args:
            user_id: User ID
            game_mode: Game mode to count
            
        Returns:
            Number of completed sessions
        """
        try:
            return self.session.query(GameSession).join(DailyWord).filter(
                and_(
                    GameSession.user_id == user_id,
                    DailyWord.game_mode == game_mode,
                    GameSession.completed == True
                )
            ).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting completed sessions for user {user_id}, mode {game_mode}: {e}")
            return 0
    
    def session_exists(self, user_id: int, daily_word_id: int) -> bool:
        """Check if game session exists for user and daily word.
        
        Args:
            user_id: User ID
            daily_word_id: Daily word ID
            
        Returns:
            True if session exists, False otherwise
        """
        try:
            return self.session.query(GameSession).filter(
                and_(
                    GameSession.user_id == user_id,
                    GameSession.daily_word_id == daily_word_id
                )
            ).count() > 0
        except SQLAlchemyError as e:
            logger.error(f"Error checking session existence for user {user_id}, daily_word {daily_word_id}: {e}")
            return False


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