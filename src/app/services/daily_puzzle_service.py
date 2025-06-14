"""Daily puzzle service for managing daily word puzzles."""

import logging
import random
from datetime import date, datetime, timezone
from typing import Optional

from ..models.game import GameMode, DailyWord, WordList
from ..repositories.game_repository import DailyWordRepository, WordListRepository

logger = logging.getLogger(__name__)


class DailyPuzzleService:
    """Service for managing daily word puzzles."""
    
    def __init__(self):
        """Initialize daily puzzle service."""
        self.daily_word_repo = DailyWordRepository()
        self.word_list_repo = WordListRepository()
    
    def get_current_date(self) -> date:
        """Get current UTC date for puzzle determination.
        
        Returns:
            Current UTC date
        """
        return datetime.now(timezone.utc).date()
    
    def get_daily_word(self, puzzle_date: date, game_mode: GameMode) -> Optional[DailyWord]:
        """Get the daily word for a specific date and game mode.
        
        Args:
            puzzle_date: Date of the puzzle
            game_mode: Game mode (classic or disney)
            
        Returns:
            DailyWord if it exists, None otherwise
        """
        try:
            return self.daily_word_repo.get_by_date_and_mode(puzzle_date, game_mode)
        except Exception as e:
            logger.error(f"Error getting daily word for {puzzle_date} {game_mode}: {e}")
            return None
    
    def get_today_puzzle(self, game_mode: GameMode) -> Optional[DailyWord]:
        """Get today's puzzle for the specified game mode.
        
        Args:
            game_mode: Game mode to get puzzle for
            
        Returns:
            Today's DailyWord if it exists, None otherwise
        """
        today = self.get_current_date()
        return self.get_daily_word(today, game_mode)
    
    def create_daily_word(self, puzzle_date: date, game_mode: GameMode, word: Optional[str] = None) -> Optional[DailyWord]:
        """Create a daily word for a specific date and game mode.
        
        Args:
            puzzle_date: Date for the puzzle
            game_mode: Game mode for the puzzle
            word: Specific word to use (if None, will select randomly)
            
        Returns:
            Created DailyWord if successful, None otherwise
        """
        try:
            # Check if daily word already exists
            existing = self.daily_word_repo.get_by_date_and_mode(puzzle_date, game_mode)
            if existing:
                logger.info(f"Daily word already exists for {puzzle_date} {game_mode}: {existing.word}")
                return existing
            
            # Select word to use
            selected_word = word
            if not selected_word:
                selected_word = self._select_random_answer_word(game_mode)
                if not selected_word:
                    logger.error(f"No answer words available for mode {game_mode}")
                    return None
            
            # Validate the word
            if not self._validate_answer_word(selected_word, game_mode):
                logger.error(f"Word {selected_word} is not valid for mode {game_mode}")
                return None
            
            # Create the daily word
            daily_word = DailyWord(
                word=selected_word.upper(),
                game_mode=game_mode,
                date=puzzle_date
            )
            
            created_word = self.daily_word_repo.create(daily_word)
            if created_word:
                logger.info(f"Created daily word for {puzzle_date} {game_mode}: {created_word.word}")
            
            return created_word
            
        except Exception as e:
            logger.error(f"Error creating daily word for {puzzle_date} {game_mode}: {e}")
            return None
    
    def create_today_puzzle(self, game_mode: GameMode, word: Optional[str] = None) -> Optional[DailyWord]:
        """Create today's puzzle for the specified game mode.
        
        Args:
            game_mode: Game mode to create puzzle for
            word: Specific word to use (if None, will select randomly)
            
        Returns:
            Created DailyWord if successful, None otherwise
        """
        today = self.get_current_date()
        return self.create_daily_word(today, game_mode, word)
    
    def ensure_today_puzzle_exists(self, game_mode: GameMode) -> Optional[DailyWord]:
        """Ensure today's puzzle exists, creating it if necessary.
        
        Args:
            game_mode: Game mode to ensure puzzle for
            
        Returns:
            Today's DailyWord (existing or newly created)
        """
        try:
            # Try to get existing puzzle
            today_puzzle = self.get_today_puzzle(game_mode)
            if today_puzzle:
                return today_puzzle
            
            # Create new puzzle
            logger.info(f"Creating today's puzzle for {game_mode.value} mode")
            return self.create_today_puzzle(game_mode)
            
        except Exception as e:
            logger.error(f"Error ensuring today's puzzle exists for {game_mode}: {e}")
            return None
    
    def get_puzzle_info(self, puzzle_date: date, game_mode: GameMode) -> dict:
        """Get puzzle information including metadata.
        
        Args:
            puzzle_date: Date of the puzzle
            game_mode: Game mode of the puzzle
            
        Returns:
            Dictionary with puzzle information
        """
        try:
            daily_word = self.get_daily_word(puzzle_date, game_mode)
            
            if not daily_word:
                return {
                    'exists': False,
                    'date': puzzle_date.isoformat(),
                    'game_mode': game_mode.value,
                    'puzzle_number': self._calculate_puzzle_number(puzzle_date, game_mode)
                }
            
            return {
                'exists': True,
                'id': daily_word.id,
                'date': daily_word.date.isoformat(),
                'game_mode': daily_word.game_mode.value,
                'word_length': len(daily_word.word),
                'puzzle_number': self._calculate_puzzle_number(puzzle_date, game_mode),
                'created_at': daily_word.created_at.isoformat() if daily_word.created_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting puzzle info for {puzzle_date} {game_mode}: {e}")
            return {
                'exists': False,
                'error': str(e)
            }
    
    def _select_random_answer_word(self, game_mode: GameMode) -> Optional[str]:
        """Select a random answer word for the given game mode.
        
        Args:
            game_mode: Game mode to select word for
            
        Returns:
            Random answer word if available, None otherwise
        """
        try:
            answer_words = self.word_list_repo.get_answer_words_by_mode(game_mode)
            if not answer_words:
                logger.warning(f"No answer words available for mode {game_mode}")
                return None
            
            # Select a random word, preferring higher frequency ranks (lower numbers)
            # Filter out words that are None or empty
            valid_words = [w for w in answer_words if w.word]
            
            if not valid_words:
                logger.warning(f"No valid answer words for mode {game_mode}")
                return None
            
            # For now, just select randomly. Later we could implement more sophisticated selection
            selected = random.choice(valid_words)
            logger.debug(f"Selected random word {selected.word} for mode {game_mode}")
            return selected.word
            
        except Exception as e:
            logger.error(f"Error selecting random answer word for mode {game_mode}: {e}")
            return None
    
    def _validate_answer_word(self, word: str, game_mode: GameMode) -> bool:
        """Validate that a word can be used as an answer for the game mode.
        
        Args:
            word: Word to validate
            game_mode: Game mode to validate against
            
        Returns:
            True if word is valid for answers, False otherwise
        """
        try:
            if not word or len(word) != 5 or not word.isalpha():
                return False
            
            normalized_word = word.upper().strip()
            return self.word_list_repo.is_answer_word(normalized_word, game_mode)
            
        except Exception as e:
            logger.error(f"Error validating answer word {word} for mode {game_mode}: {e}")
            return False
    
    def _calculate_puzzle_number(self, puzzle_date: date, game_mode: GameMode) -> int:
        """Calculate puzzle number based on date and game mode.
        
        This creates a consistent numbering system for puzzles.
        
        Args:
            puzzle_date: Date of the puzzle
            game_mode: Game mode of the puzzle
            
        Returns:
            Puzzle number (1-based)
        """
        try:
            # Use a fixed start date for each mode
            # Classic mode: January 1, 2024
            # Disney mode: January 1, 2024
            start_date = date(2024, 1, 1)
            
            if puzzle_date < start_date:
                return 1
            
            days_since_start = (puzzle_date - start_date).days
            return days_since_start + 1
            
        except Exception as e:
            logger.error(f"Error calculating puzzle number for {puzzle_date} {game_mode}: {e}")
            return 1
    
    def get_puzzle_history(self, game_mode: GameMode, limit: int = 10) -> list:
        """Get recent puzzle history for a game mode.
        
        Args:
            game_mode: Game mode to get history for
            limit: Maximum number of puzzles to return
            
        Returns:
            List of puzzle information dictionaries
        """
        try:
            # This would require a method in the repository to get recent puzzles
            # For now, we'll implement a basic version
            today = self.get_current_date()
            puzzles = []
            
            for i in range(limit):
                puzzle_date = date(today.year, today.month, today.day - i)
                if puzzle_date.day < 1:
                    break  # Simple date handling for demo
                
                puzzle_info = self.get_puzzle_info(puzzle_date, game_mode)
                if puzzle_info.get('exists'):
                    puzzles.append(puzzle_info)
            
            return puzzles
            
        except Exception as e:
            logger.error(f"Error getting puzzle history for {game_mode}: {e}")
            return []