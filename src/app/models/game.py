"""Game models for Wordle game mechanics."""

import enum
from datetime import date
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, String, Boolean, Integer, Date, JSON, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.orm import relationship, validates

from .base import BaseModel


class GameMode(enum.Enum):
    """Game mode enumeration."""
    CLASSIC = "classic"
    DISNEY = "disney"


class DailyWord(BaseModel):
    """Daily word puzzle for each game mode."""
    
    __tablename__ = "daily_words"
    
    word = Column(String(5), nullable=False, index=True)
    game_mode = Column(Enum(GameMode), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Unique constraint: one word per date per game mode
    __table_args__ = (
        UniqueConstraint('date', 'game_mode', name='uix_daily_word_date_mode'),
        Index('ix_daily_words_date_mode', 'date', 'game_mode'),
    )
    
    # Relationships
    game_sessions = relationship("GameSession", back_populates="daily_word", cascade="all, delete-orphan")
    
    @validates('word')
    def validate_word(self, key: str, word: str) -> str:
        """Validate word format.
        
        Args:
            key: Field name being validated
            word: Word to validate
            
        Returns:
            Validated word in uppercase
            
        Raises:
            ValueError: If word format is invalid
        """
        if not word or len(word) != 5:
            raise ValueError("Word must be exactly 5 characters long")
        if not word.isalpha():
            raise ValueError("Word must contain only letters")
        return word.upper()
    
    @validates('date')
    def validate_date(self, key: str, puzzle_date: date) -> date:
        """Validate puzzle date.
        
        Args:
            key: Field name being validated
            puzzle_date: Date to validate
            
        Returns:
            Validated date
            
        Raises:
            ValueError: If date is invalid
        """
        if not puzzle_date:
            raise ValueError("Date is required")
        return puzzle_date
    
    def __repr__(self) -> str:
        """String representation of daily word."""
        return f"<DailyWord(date={self.date}, mode={self.game_mode.value}, word='{self.word}')>"


class WordList(BaseModel):
    """Word list for game validation and answers."""
    
    __tablename__ = "word_list"
    
    word = Column(String(5), nullable=False, index=True)
    game_mode = Column(Enum(GameMode), nullable=False, index=True)
    is_answer = Column(Boolean, default=True, nullable=False, index=True)
    frequency_rank = Column(Integer, nullable=True)
    
    # Unique constraint: one entry per word per game mode
    __table_args__ = (
        UniqueConstraint('word', 'game_mode', name='uix_word_list_word_mode'),
        Index('ix_word_list_mode_answer', 'game_mode', 'is_answer'),
        Index('ix_word_list_frequency', 'frequency_rank'),
    )
    
    @validates('word')
    def validate_word(self, key: str, word: str) -> str:
        """Validate word format.
        
        Args:
            key: Field name being validated
            word: Word to validate
            
        Returns:
            Validated word in uppercase
            
        Raises:
            ValueError: If word format is invalid
        """
        if not word or len(word) != 5:
            raise ValueError("Word must be exactly 5 characters long")
        if not word.isalpha():
            raise ValueError("Word must contain only letters")
        return word.upper()
    
    @validates('frequency_rank')
    def validate_frequency_rank(self, key: str, rank: Optional[int]) -> Optional[int]:
        """Validate frequency rank.
        
        Args:
            key: Field name being validated
            rank: Frequency rank to validate
            
        Returns:
            Validated frequency rank
            
        Raises:
            ValueError: If rank is invalid
        """
        if rank is not None and rank < 1:
            raise ValueError("Frequency rank must be positive")
        return rank
    
    def __repr__(self) -> str:
        """String representation of word list entry."""
        return f"<WordList(word='{self.word}', mode={self.game_mode.value}, is_answer={self.is_answer})>"


class GameSession(BaseModel):
    """Game session tracking user's progress on a daily puzzle."""
    
    __tablename__ = "game_sessions"
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    daily_word_id = Column(Integer, ForeignKey('daily_words.id'), nullable=False, index=True)
    guesses = Column(JSON, default=list, nullable=False)  # [{word: "HELLO", feedback: ["correct", "absent", ...]}]
    completed = Column(Boolean, default=False, nullable=False, index=True)
    won = Column(Boolean, default=False, nullable=False, index=True)
    attempts_used = Column(Integer, default=0, nullable=False)
    
    # Unique constraint: one session per user per daily word
    __table_args__ = (
        UniqueConstraint('user_id', 'daily_word_id', name='uix_game_session_user_daily'),
        Index('ix_game_sessions_user_completed', 'user_id', 'completed'),
        Index('ix_game_sessions_daily_word', 'daily_word_id'),
    )
    
    # Relationships
    user = relationship("User", back_populates="game_sessions")
    daily_word = relationship("DailyWord", back_populates="game_sessions")
    
    @validates('guesses')
    def validate_guesses(self, key: str, guesses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate guesses format.
        
        Args:
            key: Field name being validated
            guesses: List of guess dictionaries
            
        Returns:
            Validated guesses
            
        Raises:
            ValueError: If guesses format is invalid
        """
        if not isinstance(guesses, list):
            return []
        
        # Validate each guess
        for i, guess in enumerate(guesses):
            if not isinstance(guess, dict):
                raise ValueError(f"Guess {i+1} must be a dictionary")
            if 'word' not in guess or 'feedback' not in guess:
                raise ValueError(f"Guess {i+1} must have 'word' and 'feedback' fields")
            if len(guess['word']) != 5:
                raise ValueError(f"Guess {i+1} word must be 5 characters")
            if not isinstance(guess['feedback'], list) or len(guess['feedback']) != 5:
                raise ValueError(f"Guess {i+1} feedback must be a list of 5 elements")
        
        return guesses
    
    @validates('attempts_used')
    def validate_attempts_used(self, key: str, attempts: int) -> int:
        """Validate attempts used.
        
        Args:
            key: Field name being validated
            attempts: Number of attempts used
            
        Returns:
            Validated attempts count
            
        Raises:
            ValueError: If attempts count is invalid
        """
        if attempts < 0:
            raise ValueError("Attempts used cannot be negative")
        if attempts > 6:
            raise ValueError("Attempts used cannot exceed 6")
        return attempts
    
    def add_guess(self, word: str, feedback: List[str]) -> None:
        """Add a guess to the session.
        
        Args:
            word: The guessed word
            feedback: List of feedback for each letter ("correct", "present", "absent")
        """
        if not self.guesses:
            self.guesses = []
        
        guess_data = {
            "word": word.upper(),
            "feedback": feedback
        }
        
        # Create a new list to trigger SQLAlchemy update
        new_guesses = self.guesses.copy()
        new_guesses.append(guess_data)
        self.guesses = new_guesses
        self.attempts_used = len(self.guesses)
    
    def get_current_guess_count(self) -> int:
        """Get current number of guesses made.
        
        Returns:
            Number of guesses made
        """
        return len(self.guesses) if self.guesses else 0
    
    def is_game_over(self) -> bool:
        """Check if game is over (won or max attempts reached).
        
        Returns:
            True if game is over, False otherwise
        """
        return self.completed or self.won or self.get_current_guess_count() >= 6
    
    def __repr__(self) -> str:
        """String representation of game session."""
        return f"<GameSession(user_id={self.user_id}, daily_word_id={self.daily_word_id}, won={self.won})>"


class UserStats(BaseModel):
    """User statistics for tracking game performance."""
    
    __tablename__ = "user_stats"
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    game_mode = Column(Enum(GameMode), nullable=False, index=True)
    games_played = Column(Integer, default=0, nullable=False)
    games_won = Column(Integer, default=0, nullable=False)
    current_streak = Column(Integer, default=0, nullable=False)
    max_streak = Column(Integer, default=0, nullable=False)
    guess_distribution = Column(JSON, default={"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}, nullable=False)
    
    # Unique constraint: one stats record per user per game mode
    __table_args__ = (
        UniqueConstraint('user_id', 'game_mode', name='uix_user_stats_user_mode'),
        Index('ix_user_stats_mode_games', 'game_mode', 'games_played'),
        Index('ix_user_stats_mode_wins', 'game_mode', 'games_won'),
        Index('ix_user_stats_mode_streak', 'game_mode', 'current_streak'),
    )
    
    # Relationships
    user = relationship("User", back_populates="user_stats")
    
    @validates('games_played', 'current_streak', 'max_streak')
    def validate_positive_integers(self, key: str, value: int) -> int:
        """Validate that stat values are non-negative.
        
        Args:
            key: Field name being validated
            value: Value to validate
            
        Returns:
            Validated value
            
        Raises:
            ValueError: If value is negative
        """
        if value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @validates('games_won')
    def validate_games_won(self, key: str, games_won: int) -> int:
        """Validate games won doesn't exceed games played.
        
        Args:
            key: Field name being validated
            games_won: Number of games won
            
        Returns:
            Validated games won count
            
        Raises:
            ValueError: If games won exceeds games played
        """
        if games_won < 0:
            raise ValueError("Games won cannot be negative")
        if hasattr(self, 'games_played') and games_won > self.games_played:
            raise ValueError("Games won cannot exceed games played")
        return games_won
    
    @validates('guess_distribution')
    def validate_guess_distribution(self, key: str, distribution: Dict[str, int]) -> Dict[str, int]:
        """Validate guess distribution format.
        
        Args:
            key: Field name being validated
            distribution: Guess distribution dictionary
            
        Returns:
            Validated guess distribution
            
        Raises:
            ValueError: If distribution format is invalid
        """
        if not isinstance(distribution, dict):
            return {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}
        
        # Ensure all required keys exist
        required_keys = {"1", "2", "3", "4", "5", "6"}
        for key_str in required_keys:
            if key_str not in distribution:
                distribution[key_str] = 0
            elif not isinstance(distribution[key_str], int) or distribution[key_str] < 0:
                distribution[key_str] = 0
        
        return distribution
    
    def get_win_percentage(self) -> float:
        """Calculate win percentage.
        
        Returns:
            Win percentage as a float (0-100)
        """
        if self.games_played == 0:
            return 0.0
        return round((self.games_won / self.games_played) * 100, 1)
    
    def update_stats(self, won: bool, attempts_used: int) -> None:
        """Update statistics after a game.
        
        Args:
            won: Whether the game was won
            attempts_used: Number of attempts used (1-6)
        """
        self.games_played += 1
        
        if won:
            self.games_won += 1
            self.current_streak += 1
            self.max_streak = max(self.max_streak, self.current_streak)
            
            # Update guess distribution
            if 1 <= attempts_used <= 6:
                distribution = self.guess_distribution.copy()
                distribution[str(attempts_used)] = distribution.get(str(attempts_used), 0) + 1
                self.guess_distribution = distribution
        else:
            self.current_streak = 0
    
    def get_average_guesses(self) -> float:
        """Calculate average guesses for won games.
        
        Returns:
            Average number of guesses for won games
        """
        if self.games_won == 0:
            return 0.0
        
        total_guesses = 0
        for attempts, count in self.guess_distribution.items():
            total_guesses += int(attempts) * count
        
        return round(total_guesses / self.games_won, 1)
    
    def __repr__(self) -> str:
        """String representation of user stats."""
        return f"<UserStats(user_id={self.user_id}, mode={self.game_mode.value}, win_rate={self.get_win_percentage()}%)>" 