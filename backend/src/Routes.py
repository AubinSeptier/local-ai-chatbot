from flask import request, Response, session, jsonify
from flask import stream_with_context

from functools import wraps
import asyncio
import uuid
import logging
from typing import Any, Dict, Generator

logger = logging.getLogger(__name__)

def login_required(f: callable) -> callable:
    """
    Decorator to ensure user is authenticated.
    
    Args:
        f (callable): Route function to protect
        
    Returns:
        callable: Wrapped route function
    """
    @wraps(f)
    def decorated(*args, **kwargs) -> Any:
        if 'user_id' not in session:
            logger.warning("Unauthorized access attempt")
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

def register_routes(app: Any, chat_api: Any, db: Any) -> None:
    """
    Register all application routes.
    
    Args:
        app (Flask): Flask application instance
        chat_api (ChatAPI): Chat API handler instance
        db (Database): Database connection instance
    """
    
    @app.route('/api/register', methods=['POST'])
    def register() -> Response:
        """
        Handle user registration.
        
        Request JSON:
        {
            "username": "string",
            "password": "string"
        }
        
        Returns:
            JSON response with status and message
        """
        try:
            data: Dict = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
                
            username: str = data.get('username', '').strip()
            password: str = data.get('password', '').strip()
            
            if not username or not password:
                return jsonify({"error": "Username and password required"}), 400
                
            if db.add_user(username, password):
                user_id: int = db.verify_user(username, password)
                session['user_id'] = user_id
                session['username'] = username
                logger.info(f"New user registered: {username}")
                return jsonify({"message": "Registration successful"})
                
            return jsonify({"error": "Username already exists"}), 400
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/login', methods=['POST'])
    def login() -> Response:
        """
        Handle user login.
        
        Request JSON:
        {
            "username": "string",
            "password": "string"
        }
        
        Returns:
            JSON response with status and message
        """
        try:
            data: Dict = request.get_json()
            username: str = data.get('username', '').strip()
            password: str = data.get('password', '').strip()
            
            user_id: int = db.verify_user(username, password)
            if user_id:
                session['user_id'] = user_id
                session['username'] = username
                logger.info(f"User logged in: {username}")
                return jsonify({"message": "Login successful"})
                
            logger.warning(f"Failed login attempt for: {username}")
            return jsonify({"error": "Invalid credentials"}), 401
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/logout', methods=['POST'])
    def logout() -> Response:
        """Handle user logout."""
        session.clear()
        return jsonify({"message": "Logout successful"})
    
    @app.route('/api/check-auth', methods=['GET'])
    def check_auth() -> Response:
        """Check authentication status."""
        if 'user_id' in session:
            return jsonify({"authenticated": True})
        return jsonify({"authenticated": False}), 401

    @app.route('/api/conversations', methods=['GET'])
    @login_required
    def get_conversations() -> Response:
        """
        Get list of user's conversations.
        
        Returns:
            JSON list of conversations with metadata
        """
        try:
            user_id: int = session['user_id']
            return jsonify({
                "conversations": db.get_user_conversations(user_id)
            })
        except Exception as e:
            logger.error(f"Conversation list error: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/conversations', methods=['POST'])
    @login_required
    def create_conversation() -> Response:
        """
        Create a new conversation.
        
        Returns:
            JSON response with new conversation ID
        """
        conversation_id: str = str(uuid.uuid4())
        db.add_conversation(session['user_id'], conversation_id, "New Conversation")
        return jsonify({"conversation_id": conversation_id})

    @app.route('/api/chat', methods=['POST'])
    @login_required
    def chat() -> Response:
        """
        Handle chat requests with streaming response.
        
        Request JSON:
        {
            "message": "string",
            "conversation_id": "string"
        }
        
        Returns:
            EventSource stream with chat response
        """
        try:
            data: Dict = request.get_json()
            message: str = data.get('message', '').strip()
            conversation_id: str = data.get('conversation_id', str(uuid.uuid4()))
            user_id: int = session['user_id']

            if not message:
                return jsonify({"error": "Empty message"}), 400

            def sync_stream() -> Generator:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                async_gen = chat_api.stream_response(message, user_id, conversation_id)
                
                try:
                    while True:
                        token = loop.run_until_complete(async_gen.__anext__())
                        yield token
                except StopAsyncIteration:
                    pass
                finally:
                    loop.close()

            return Response(
                stream_with_context(sync_stream()),
                mimetype='text/event-stream'
            )

        except Exception as e:
            logger.error(f"Chat endpoint error: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/conversations/<conversation_id>/history', methods=['GET'])
    @login_required
    def get_conversation_history(conversation_id: str) -> Response:
        """
        Get conversation history.
        
        Args:
            conversation_id (str): Conversation identifier
            
        Returns:
            JSON list of historical messages
        """
        try:
            user_id: int = session['user_id']
            conversation = chat_api.get_conversation(user_id, conversation_id)
            return jsonify({
                "history": conversation.get_history(),
                "conversation_id": conversation_id
            })
        except Exception as e:
            logger.error(f"History error: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/conversations/<conversation_id>/title', methods=['POST'])
    @login_required
    def update_conversation_title(conversation_id: str) -> Response:
        """
        Update conversation title.
        
        Request JSON:
        {
            "first_message": "string"
        }
        """
        try:
            data: Dict = request.get_json()
            first_message: str = data.get('first_message', '')
            title: str = chat_api.generate_conversation_title(first_message)
            db.update_conversation_title(conversation_id, title)
            return jsonify({"title": title})
        except Exception as e:
            logger.error(f"Title update error: {str(e)}")
            return jsonify({"error": str(e)}), 500