"""Database indexing optimization for performance."""

from sqlalchemy import Index, text
from ..models.user import User
from ..models.game import DailyWord, WordList, GameSession, UserStats


def create_performance_indexes(db):
    """Create database indexes for better query performance."""
    
    # User model indexes
    user_email_idx = Index('idx_users_email', User.email)
    user_username_idx = Index('idx_users_username', User.username)
    
    # Daily word indexes
    daily_word_date_mode_idx = Index(
        'idx_daily_words_date_mode', 
        DailyWord.date, 
        DailyWord.game_mode
    )
    daily_word_mode_date_idx = Index(
        'idx_daily_words_mode_date',
        DailyWord.game_mode,
        DailyWord.date.desc()
    )
    
    # Word list indexes
    word_list_word_mode_idx = Index(
        'idx_word_list_word_mode',
        WordList.word,
        WordList.game_mode
    )
    word_list_mode_answer_idx = Index(
        'idx_word_list_mode_answer',
        WordList.game_mode,
        WordList.is_answer
    )
    word_list_mode_freq_idx = Index(
        'idx_word_list_mode_freq',
        WordList.game_mode,
        WordList.frequency_rank
    )
    
    # Game session indexes
    game_session_user_idx = Index(
        'idx_game_sessions_user',
        GameSession.user_id
    )
    game_session_daily_word_idx = Index(
        'idx_game_sessions_daily_word',
        GameSession.daily_word_id
    )
    game_session_user_daily_idx = Index(
        'idx_game_sessions_user_daily',
        GameSession.user_id,
        GameSession.daily_word_id
    )
    game_session_completed_idx = Index(
        'idx_game_sessions_completed',
        GameSession.completed,
        GameSession.created_at.desc()
    )
    game_session_user_created_idx = Index(
        'idx_game_sessions_user_created',
        GameSession.user_id,
        GameSession.created_at.desc()
    )
    
    # User stats indexes
    user_stats_user_mode_idx = Index(
        'idx_user_stats_user_mode',
        UserStats.user_id,
        UserStats.game_mode
    )
    user_stats_mode_wins_idx = Index(
        'idx_user_stats_mode_wins',
        UserStats.game_mode,
        UserStats.games_won.desc()
    )
    user_stats_mode_percentage_idx = Index(
        'idx_user_stats_mode_percentage',
        UserStats.game_mode,
        UserStats.win_percentage.desc()
    )
    user_stats_mode_streak_idx = Index(
        'idx_user_stats_mode_streak',
        UserStats.game_mode,
        UserStats.current_streak.desc()
    )
    
    # Timestamp indexes for all models (for auditing and cleanup)
    user_created_idx = Index('idx_users_created', User.created_at.desc())
    game_session_created_idx = Index('idx_game_sessions_created', GameSession.created_at.desc())
    user_stats_updated_idx = Index('idx_user_stats_updated', UserStats.updated_at.desc())
    
    # Create all indexes
    indexes = [
        # User indexes
        user_email_idx,
        user_username_idx,
        user_created_idx,
        
        # Daily word indexes
        daily_word_date_mode_idx,
        daily_word_mode_date_idx,
        
        # Word list indexes
        word_list_word_mode_idx,
        word_list_mode_answer_idx,
        word_list_mode_freq_idx,
        
        # Game session indexes
        game_session_user_idx,
        game_session_daily_word_idx,
        game_session_user_daily_idx,
        game_session_completed_idx,
        game_session_user_created_idx,
        game_session_created_idx,
        
        # User stats indexes
        user_stats_user_mode_idx,
        user_stats_mode_wins_idx,
        user_stats_mode_percentage_idx,
        user_stats_mode_streak_idx,
        user_stats_updated_idx
    ]
    
    return indexes


def create_database_views(db):
    """Create database views for complex queries."""
    
    # View for leaderboard queries
    leaderboard_view = """
    CREATE OR REPLACE VIEW leaderboard_view AS
    SELECT 
        us.user_id,
        u.username,
        us.game_mode,
        us.games_played,
        us.games_won,
        us.win_percentage,
        us.current_streak,
        us.max_streak,
        RANK() OVER (PARTITION BY us.game_mode ORDER BY us.win_percentage DESC, us.games_won DESC) as win_rank,
        RANK() OVER (PARTITION BY us.game_mode ORDER BY us.current_streak DESC, us.win_percentage DESC) as streak_rank,
        RANK() OVER (PARTITION BY us.game_mode ORDER BY us.games_won DESC, us.win_percentage DESC) as wins_rank
    FROM user_stats us
    JOIN users u ON us.user_id = u.id
    WHERE us.games_played >= 3  -- Minimum games for leaderboard inclusion
    """
    
    # View for game history with puzzle info
    game_history_view = """
    CREATE OR REPLACE VIEW game_history_view AS
    SELECT 
        gs.id as session_id,
        gs.user_id,
        u.username,
        gs.completed,
        gs.won,
        gs.attempts_used,
        gs.guesses,
        gs.created_at as game_date,
        dw.word as target_word,
        dw.game_mode,
        dw.date as puzzle_date,
        EXTRACT(EPOCH FROM (gs.updated_at - gs.created_at)) as duration_seconds
    FROM game_sessions gs
    JOIN users u ON gs.user_id = u.id
    JOIN daily_words dw ON gs.daily_word_id = dw.id
    ORDER BY gs.created_at DESC
    """
    
    # View for daily statistics
    daily_stats_view = """
    CREATE OR REPLACE VIEW daily_stats_view AS
    SELECT 
        dw.date,
        dw.game_mode,
        dw.word as puzzle_word,
        COUNT(gs.id) as total_attempts,
        COUNT(CASE WHEN gs.completed = true THEN 1 END) as completed_games,
        COUNT(CASE WHEN gs.won = true THEN 1 END) as won_games,
        ROUND(
            COUNT(CASE WHEN gs.won = true THEN 1 END)::float / 
            NULLIF(COUNT(CASE WHEN gs.completed = true THEN 1 END), 0) * 100, 
            2
        ) as win_percentage,
        ROUND(AVG(CASE WHEN gs.won = true THEN gs.attempts_used END), 2) as avg_attempts_when_won
    FROM daily_words dw
    LEFT JOIN game_sessions gs ON dw.id = gs.daily_word_id
    GROUP BY dw.date, dw.game_mode, dw.word
    ORDER BY dw.date DESC, dw.game_mode
    """
    
    views = [
        leaderboard_view,
        game_history_view,
        daily_stats_view
    ]
    
    return views


def apply_database_optimizations(db):
    """Apply all database optimizations."""
    try:
        # Create indexes
        indexes = create_performance_indexes(db)
        for index in indexes:
            try:
                index.create(db.engine, checkfirst=True)
                print(f"✅ Created index: {index.name}")
            except Exception as e:
                print(f"⚠️ Index {index.name} already exists or failed: {e}")
        
        # Create views
        views = create_database_views(db)
        for view_sql in views:
            try:
                db.session.execute(text(view_sql))
                db.session.commit()
                print(f"✅ Created database view")
            except Exception as e:
                print(f"⚠️ View creation failed or already exists: {e}")
                db.session.rollback()
        
        print("🚀 Database optimizations applied successfully!")
        
    except Exception as e:
        print(f"❌ Error applying database optimizations: {e}")
        raise


def get_query_performance_tips():
    """Get query performance optimization tips."""
    return {
        "tips": [
            "Use indexes on frequently queried columns",
            "Avoid SELECT * queries, specify needed columns",
            "Use LIMIT for pagination instead of loading all records",
            "Consider caching for frequently accessed data",
            "Use database views for complex repeated queries",
            "Monitor slow queries and optimize them",
            "Use connection pooling for concurrent requests",
            "Consider read replicas for heavy read workloads"
        ],
        "query_patterns": {
            "efficient_user_lookup": "SELECT id, username FROM users WHERE email = ? LIMIT 1",
            "efficient_daily_puzzle": "SELECT * FROM daily_words WHERE date = ? AND game_mode = ? LIMIT 1",
            "efficient_word_validation": "SELECT 1 FROM word_list WHERE word = ? AND game_mode = ? LIMIT 1",
            "efficient_leaderboard": "SELECT * FROM leaderboard_view WHERE game_mode = ? LIMIT 10"
        }
    }