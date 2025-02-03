from flask import Flask
from flask_cors import CORS
from ChatApi import ChatAPI
from Routes import register_routes

def create_app(config=None):
    """
    Create and configure the Flask application.
    """
    app = Flask(__name__)
    CORS(app)

    # Configuration
    generation_config = {
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_k": 50,
        "top_p": 0.95,
        # ... other generation parameters
    }

    # Initialize ChatAPI
    chat_api = ChatAPI(
        model_name="unsloth/Llama-3.2-3B-Instruct-bnb-4bit",
        generation_config=generation_config,
        max_history=100,
        system_prompt="You are a helpful assistant."
    )

    # Register routes
    register_routes(app, chat_api)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=7860, debug=True, use_reloader=False)