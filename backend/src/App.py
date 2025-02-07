from flask import Flask
from flask_cors import CORS
from ChatApi import ChatAPI
from Routes import register_routes
from Database import Database
import os
import secrets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """
    Factory function to create and configure the Flask application.
    """
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, 
         supports_credentials=True,
         resources={
             r"/*": {
                 "origins": ["http://localhost:5173"],
                 "methods": ["GET", "POST", "OPTIONS", "DELETE"],
                 "allow_headers": ["Content-Type"],
                 "supports_credentials": True
             }
         })
    
    # Application configuration
    app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
    app.config.update({
        'PERMANENT_SESSION_LIFETIME': 86400,  # 24 hours
        'SESSION_COOKIE_SECURE': False,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': 'Lax'
    })
    
    # Database setup
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../instance', 'chat_app.db')
    os.makedirs(app.instance_path, exist_ok=True)
    db = Database(db_path)

    # Model configuration
    generation_config = {
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_k": 50,
        "top_p": 0.95
        # ... other generation parameters
    }

    # Initialize Chat API
    chat_api = ChatAPI(
        model_name="unsloth/Llama-3.2-3B-Instruct-bnb-4bit",
        generation_config=generation_config,
        max_history=100,
        system_prompt="You are a helpful assistant.",
        db=db
    )

    # Register routes
    register_routes(app, chat_api, db)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=7860, debug=False)