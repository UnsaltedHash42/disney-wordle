"""Application entry point."""

import os
import argparse
from dotenv import load_dotenv

from src.app import create_app

# Load environment variables
load_dotenv()

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Wordle Flask application')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 8000)), 
                       help='Port to bind to (default: 8000)')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode (default: from config)')
    
    args = parser.parse_args()
    
    # Run development server
    print(f"🚀 Starting Wordle application on http://{args.host}:{args.port}")
    print(f"📝 Game modes: Classic Wordle & Disney Wordle")
    print(f"♿ Color-blind accessible design included")
    print(f"📱 Mobile responsive interface ready")
    print("-" * 50)
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug if args.debug else app.config.get('DEBUG', False)
    ) 