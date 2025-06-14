"""Database indexing optimization for performance."""

from sqlalchemy import Index, text
from ..models.user import User
from ..models.game import WordList, GameSession, UserStats


def create_performance_indexes(db):
    """Create database indexes for better query performance."""
    
    # User model indexes
    user_email_idx = Index('idx_users_email', User.email)
    user_username_idx = Index('idx_users_username', User.username)
    
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
    user_stats_mode_streak_idx = Index(
        'idx_user_stats_mode_streak',
        UserStats.game_mode,
        UserStats.current_streak.desc()
    )
    user_stats_updated_idx = Index('idx_user_stats_updated', UserStats.updated_at.desc())
    
    # Timestamp indexes for all models (for auditing and cleanup)
    user_created_idx = Index('idx_users_created', User.created_at.desc())
    game_session_created_idx = Index('idx_game_sessions_created', GameSession.created_at.desc())
    
    # Create all indexes
    indexes = [
        # User indexes
        user_email_idx,
        user_username_idx,
        user_created_idx,
        
        # Word list indexes
        word_list_word_mode_idx,
        word_list_mode_answer_idx,
        word_list_mode_freq_idx,
        
        # Game session indexes
        game_session_user_idx,
        game_session_completed_idx,
        game_session_user_created_idx,
        game_session_created_idx,
        
        # User stats indexes
        user_stats_user_mode_idx,
        user_stats_mode_wins_idx,
        user_stats_mode_streak_idx,
        user_stats_updated_idx
    ]
    
    return indexes


def create_database_views(db):
    """Create database views for complex queries."""
    
    # Remove or update all view creation for leaderboard_view, game_history_view, daily_stats_view
    # These reference daily_words and daily_word_id, which are now gone
    # TODO: Redesign views for unlimited play model
    
    views = []
    
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