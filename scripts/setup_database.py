#!/usr/bin/env python3
"""
Database setup and optimization script for Wordle application.
Applies indexes, views, and performance optimizations.
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from app import create_app
from app.database import db
from app.database.indexes import apply_database_optimizations, get_query_performance_tips
from app.utils.caching import CacheManager


def setup_database():
    """Set up database with optimizations."""
    app = create_app()
    
    with app.app_context():
        print("🔧 Setting up database optimizations...")
        
        # Apply database optimizations
        apply_database_optimizations(db)
        
        # Warm up cache
        print("🔥 Warming up application cache...")
        CacheManager.warm_cache()
        
        # Display performance tips
        tips = get_query_performance_tips()
        print("\n📈 Query Performance Tips:")
        for tip in tips['tips']:
            print(f"   • {tip}")
        
        print("\n✅ Database setup completed successfully!")
        print("\n🚀 Your Wordle application is now optimized for production!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Set up and optimize Wordle database')
    args = parser.parse_args()
    
    setup_database()


if __name__ == "__main__":
    main()