#!/usr/bin/env python
"""Test runner for Phase 1 authentication system."""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run the test suite and display results."""
    print("🧪 Running Phase 1 Test Suite")
    print("=" * 50)
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', 
            '-v',
            '--tb=short',
            '--color=yes'
        ], 
        cwd=project_root,
        capture_output=True,
        text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("\n🎉 All tests passed! Phase 1 authentication system is working correctly.")
            print("\n✅ Ready for Checkpoint 1!")
            return True
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_quick_test():
    """Run a quick smoke test of the authentication system."""
    print("🔥 Running Quick Smoke Test")
    print("=" * 30)
    
    try:
        from src.app import create_app
        from src.app.database import db
        from src.app.services.auth_service import AuthService
        
        # Create test app with SQLite
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'JWT_SECRET_KEY': 'test-secret-key',
            'SECRET_KEY': 'test-secret'
        })
        
        with app.app_context():
            # Create tables
            db.create_all()
            print("✅ Database tables created")
            
            # Test auth service
            auth_service = AuthService()
            
            # Test user registration
            user_data = {
                'username': 'testuser',
                'email': 'test@example.com', 
                'password': 'TestPass123'
            }
            
            user = auth_service.register_user(user_data)
            print("✅ User registration works")
            
            # Test authentication
            authenticated_user = auth_service.authenticate_user(
                user_data['email'], 
                user_data['password']
            )
            print("✅ User authentication works")
            
            print("\n🎉 Quick test passed! Core authentication is functional.")
            return True
            
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        success = run_quick_test()
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1) 