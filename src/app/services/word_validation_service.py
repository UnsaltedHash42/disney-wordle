"""Word validation service for game mechanics."""

import logging
from typing import Optional

from ..models.game import GameMode, WordList
from ..repositories.game_repository import WordListRepository

logger = logging.getLogger(__name__)


class WordValidationService:
    """Service for validating words and managing word lists."""
    
    def __init__(self):
        """Initialize word validation service."""
        self.word_repo = WordListRepository()
    
    def is_valid_guess(self, word: str, game_mode: GameMode) -> bool:
        """Check if a word is valid for guessing in the given game mode.
        
        Args:
            word: Word to validate (will be normalized to uppercase)
            game_mode: Game mode to validate against
            
        Returns:
            True if word is valid for guessing, False otherwise
        """
        try:
            if not word or len(word) != 5:
                logger.debug(f"Invalid word length: {word}")
                return False
            
            if not word.isalpha():
                return False
            
            normalized_word = word.upper().strip()
            is_valid = self.word_repo.is_valid_word(normalized_word, game_mode)
            
            logger.debug(f"Word validation: {normalized_word} in {game_mode.value} = {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating word {word} for mode {game_mode}: {e}")
            return False
    
    def is_answer_word(self, word: str, game_mode: GameMode) -> bool:
        """Check if a word can be used as an answer in the given game mode.
        
        Args:
            word: Word to check (will be normalized to uppercase)
            game_mode: Game mode to check against
            
        Returns:
            True if word can be an answer, False otherwise
        """
        try:
            if not word or len(word) != 5:
                return False
            
            if not word.isalpha():
                return False
            
            normalized_word = word.upper().strip()
            is_answer = self.word_repo.is_answer_word(normalized_word, game_mode)
            
            logger.debug(f"Answer word check: {normalized_word} in {game_mode.value} = {is_answer}")
            return is_answer
            
        except Exception as e:
            logger.error(f"Error checking answer word {word} for mode {game_mode}: {e}")
            return False
    
    def validate_word_format(self, word: str) -> tuple[bool, str]:
        """Validate basic word format requirements.
        
        Args:
            word: Word to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not word:
            return False, "Word cannot be empty"
        
        if len(word) != 5:
            return False, "Word must be exactly 5 characters long"
        
        if not word.isalpha():
            return False, "Word must contain only letters"
        
        return True, ""