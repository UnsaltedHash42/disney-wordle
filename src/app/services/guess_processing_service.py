"""Guess processing service for generating Wordle feedback."""

import logging
from typing import List, Dict, Any
from collections import Counter

logger = logging.getLogger(__name__)


class GuessProcessingService:
    """Service for processing guesses and generating feedback."""
    
    # Feedback constants
    CORRECT = "correct"     # Letter is in the correct position (green)
    PRESENT = "present"     # Letter is in the word but wrong position (yellow)
    ABSENT = "absent"       # Letter is not in the word (gray)
    
    def __init__(self):
        """Initialize guess processing service."""
        pass
    
    def process_guess(self, guess: str, target_word: str) -> List[str]:
        """Process a guess against the target word and generate feedback.
        
        This implements the standard Wordle feedback algorithm:
        - Green (correct): Letter is in the correct position
        - Yellow (present): Letter is in the word but wrong position
        - Gray (absent): Letter is not in the word
        
        Args:
            guess: The guessed word (5 letters)
            target_word: The target word to compare against (5 letters)
            
        Returns:
            List of feedback strings for each letter position
            
        Raises:
            ValueError: If guess or target word are invalid
        """
        try:
            # Validate inputs
            if not self._validate_word(guess):
                raise ValueError(f"Invalid guess: {guess}")
            if not self._validate_word(target_word):
                raise ValueError(f"Invalid target word: {target_word}")
            
            # Normalize to uppercase
            guess = guess.upper().strip()
            target = target_word.upper().strip()
            
            logger.debug(f"Processing guess '{guess}' against target '{target}'")
            
            # Initialize feedback array
            feedback = [self.ABSENT] * 5
            
            # Count letters in target word for handling duplicates correctly
            target_letter_counts = Counter(target)
            used_target_letters = Counter()
            
            # First pass: Mark all correct positions (green)
            for i in range(5):
                if guess[i] == target[i]:
                    feedback[i] = self.CORRECT
                    used_target_letters[guess[i]] += 1
            
            # Second pass: Mark present letters (yellow) and absent letters (gray)
            for i in range(5):
                if feedback[i] == self.CORRECT:
                    continue  # Already marked as correct
                
                guess_letter = guess[i]
                
                # Check if letter exists in target and we haven't used all instances
                if (guess_letter in target_letter_counts and 
                    used_target_letters[guess_letter] < target_letter_counts[guess_letter]):
                    feedback[i] = self.PRESENT
                    used_target_letters[guess_letter] += 1
                else:
                    feedback[i] = self.ABSENT
            
            logger.debug(f"Generated feedback: {feedback}")
            return feedback
            
        except Exception as e:
            logger.error(f"Error processing guess '{guess}' against '{target_word}': {e}")
            raise
    
    def create_guess_result(self, guess: str, target_word: str) -> Dict[str, Any]:
        """Create a complete guess result with word and feedback.
        
        Args:
            guess: The guessed word
            target_word: The target word to compare against
            
        Returns:
            Dictionary containing guess word and feedback
        """
        try:
            feedback = self.process_guess(guess, target_word)
            
            return {
                "word": guess.upper().strip(),
                "feedback": feedback
            }
            
        except Exception as e:
            logger.error(f"Error creating guess result for '{guess}': {e}")
            raise
    
    def is_winning_guess(self, feedback: List[str]) -> bool:
        """Check if a guess feedback indicates a win (all correct).
        
        Args:
            feedback: List of feedback strings from process_guess
            
        Returns:
            True if all positions are correct, False otherwise
        """
        return all(fb == self.CORRECT for fb in feedback)
    
    def is_valid_word_format(self, word: str) -> bool:
        """Check if a word has valid format for the game.
        
        Args:
            word: Word to validate
            
        Returns:
            True if word format is valid, False otherwise
        """
        return self._validate_word(word)
    
    def get_letter_status(self, guesses_with_feedback: List[Dict[str, Any]], letter: str) -> str:
        """Get the status of a letter based on all previous guesses.
        
        This is useful for updating keyboard colors in the UI.
        
        Args:
            guesses_with_feedback: List of guess dictionaries with feedback
            letter: Letter to check status for
            
        Returns:
            Status string: 'correct', 'present', 'absent', or 'unknown'
        """
        try:
            letter = letter.upper()
            best_status = "unknown"
            
            # Priority: correct > present > absent > unknown
            status_priority = {
                "unknown": 0,
                self.ABSENT: 1,
                self.PRESENT: 2,
                self.CORRECT: 3
            }
            
            for guess_data in guesses_with_feedback:
                word = guess_data.get("word", "")
                feedback = guess_data.get("feedback", [])
                
                for i, (guess_letter, status) in enumerate(zip(word, feedback)):
                    if guess_letter == letter:
                        if status_priority[status] > status_priority[best_status]:
                            best_status = status
            
            return best_status
            
        except Exception as e:
            logger.error(f"Error getting letter status for '{letter}': {e}")
            return "unknown"
    
    def get_keyboard_status(self, guesses_with_feedback: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get status of all letters for keyboard display.
        
        Args:
            guesses_with_feedback: List of guess dictionaries with feedback
            
        Returns:
            Dictionary mapping each letter to its status
        """
        try:
            keyboard_status = {}
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            
            for letter in alphabet:
                keyboard_status[letter] = self.get_letter_status(guesses_with_feedback, letter)
            
            return keyboard_status
            
        except Exception as e:
            logger.error(f"Error getting keyboard status: {e}")
            return {}
    
    def analyze_guess_quality(self, guess: str, target_word: str, feedback: List[str]) -> Dict[str, Any]:
        """Analyze the quality of a guess for statistics or hints.
        
        Args:
            guess: The guessed word
            target_word: The target word
            feedback: Feedback from processing the guess
            
        Returns:
            Dictionary with analysis metrics
        """
        try:
            correct_letters = sum(1 for fb in feedback if fb == self.CORRECT)
            present_letters = sum(1 for fb in feedback if fb == self.PRESENT)
            absent_letters = sum(1 for fb in feedback if fb == self.ABSENT)
            
            # Calculate common letters
            guess_set = set(guess.upper())
            target_set = set(target_word.upper())
            common_letters = len(guess_set.intersection(target_set))
            
            return {
                "correct_positions": correct_letters,
                "present_letters": present_letters,
                "absent_letters": absent_letters,
                "common_letters": common_letters,
                "is_winning": self.is_winning_guess(feedback),
                "quality_score": (correct_letters * 3 + present_letters) / 15  # 0-1 scale
            }
            
        except Exception as e:
            logger.error(f"Error analyzing guess quality: {e}")
            return {}
    
    def _validate_word(self, word: str) -> bool:
        """Validate that a word is properly formatted for the game.
        
        Args:
            word: Word to validate
            
        Returns:
            True if word is valid, False otherwise
        """
        if not word:
            return False
        
        word = word.strip()
        
        if len(word) != 5:
            return False
        
        if not word.isalpha():
            return False
        
        return True
    
    def simulate_game(self, target_word: str, guesses: List[str]) -> Dict[str, Any]:
        """Simulate a complete game with multiple guesses.
        
        This is useful for testing or analysis.
        
        Args:
            target_word: The target word
            guesses: List of guess words
            
        Returns:
            Dictionary with complete game simulation results
        """
        try:
            results = []
            won = False
            
            for i, guess in enumerate(guesses):
                if won:
                    break  # Stop processing if already won
                
                guess_result = self.create_guess_result(guess, target_word)
                results.append(guess_result)
                
                if self.is_winning_guess(guess_result["feedback"]):
                    won = True
            
            return {
                "target_word": target_word.upper(),
                "guesses": results,
                "won": won,
                "attempts_used": len(results),
                "keyboard_status": self.get_keyboard_status(results)
            }
            
        except Exception as e:
            logger.error(f"Error simulating game with target '{target_word}': {e}")
            raise