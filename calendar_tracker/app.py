from flask import Flask
from flask_cors import CORS
from routes import main_bp
from models import init_db
from dotenv import load_dotenv
import os

def create_app():
    """Create and configure the Flask application"""
    # Load environment variables once at startup
    load_dotenv()

    # Check for required environment variables
    required_vars = ['FLASK_SECRET_KEY', 'GEMINI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"Warning: Missing required environment variables: {', '.join(missing_vars)}")
    
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    # Configure app
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key_here')
    app.config['JSON_SORT_KEYS'] = False

    # Register the blueprint containing all routes
    app.register_blueprint(main_bp)

    return app

# Initialize app
app = create_app()

# Initialize database if running directly
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
