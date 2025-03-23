from flask import Flask
from flask_cors import CORS
from flask_session import Session
from datetime import timedelta
from routes import main_bp
from models import init_db
from dotenv import load_dotenv
import os

def create_app():
    """Create and configure the Flask application"""
    # Load environment variables once at startup
    load_dotenv()

    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    # Configure app and session
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key_here')
    app.config['JSON_SORT_KEYS'] = False
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

    # Initialize Flask-Session
    Session(app)

    # Check environment and service status
    gemini_status = {
        'available': True,
        'message': 'Gemini AI service is operational',
        'mode': 'normal'
    }

    # Check for required environment variables
    required_vars = ['FLASK_SECRET_KEY', 'GEMINI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Warning: Missing required environment variables: {', '.join(missing_vars)}")
        gemini_status.update({
            'available': False,
            'message': f"Missing configuration: {', '.join(missing_vars)}",
            'mode': 'fallback'
        })
        # Log the status
        with open('gemini_errors.log', 'a') as f:
            f.write(f"[{os.path.basename(__file__)}] Application started in fallback mode - Missing: {', '.join(missing_vars)}\n")

    # Make service status available to all routes
    @app.context_processor
    def inject_gemini_status():
        return {'gemini_status': gemini_status}

    # Add error handlers
    @app.errorhandler(500)
    def handle_error(error):
        error_msg = f"Internal error: {str(error)}"
        # Log the error
        with open('gemini_errors.log', 'a') as f:
            f.write(f"[{os.path.basename(__file__)}] 500 Error: {error_msg}\n")
        return {
            "error": error_msg,
            "status": gemini_status,
            "message": "The application is running in fallback mode"
        }, 500

    @app.errorhandler(404)
    def not_found_error(error):
        return {
            "error": "Resource not found",
            "status": gemini_status,
            "message": "The requested resource was not found"
        }, 404

    # Register the blueprint containing all routes
    app.register_blueprint(main_bp)

    return app

# Initialize app
app = create_app()

# Initialize database if running directly
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
