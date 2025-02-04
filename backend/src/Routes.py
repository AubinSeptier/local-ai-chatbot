from flask import request, Response, stream_with_context, session, jsonify
from langchain_core.messages import HumanMessage
from functools import wraps
import json
import asyncio
import logging
import uuid
from query_data import query_rag

logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

def register_routes(app, chat_api, db):
    """
    Register all routes for the application.
    """
    
    @app.route('/api/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            
            logger.info(f"Attempting to register user: {username}")
            
            if db.add_user(username, password):
                user_id = db.verify_user(username, password)
                session['user_id'] = user_id
                session['username'] = username
                logger.info(f"Successfully registered and logged in user: {username}")
                return jsonify({'message': 'User registered and logged in successfully'})
            
            logger.warning(f"Registration failed - username already exists: {username}")
            return jsonify({'error': 'Username already exists'}), 400
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
                
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            
            logger.info(f"Login attempt for user: {username}")
            
            user_id = db.verify_user(username, password)
            if user_id:
                session['user_id'] = user_id
                session['username'] = username
                logger.info(f"Successful login for user: {username}")
                return jsonify({'message': 'Login successful'})
            
            logger.warning(f"Failed login attempt for user: {username}")
            return jsonify({'error': 'Invalid credentials'}), 401
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/logout', methods=['POST'])
    def logout():
        session.clear()
        return jsonify({'message': 'Logged out successfully'})
    
    @app.route('/api/check-auth', methods=['GET'])
    def check_auth():
        try:
            if 'user_id' in session:
                logger.debug(f"Auth check: authenticated user_id={session['user_id']}")
                return jsonify({'authenticated': True})
            logger.debug("Auth check: no authenticated user")
            return jsonify({'authenticated': False}), 401
        except Exception as e:
            logger.error(f"Auth check error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    @app.route('/api/conversations', methods=['GET'])
    @login_required
    def get_conversations():
        try:
            user_id = session['user_id']
            conversations = db.get_user_conversations(user_id)
            logger.debug(f"Retrieved conversations for user {user_id}: {conversations}")
            return jsonify({'conversations': conversations})
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/conversations', methods=['POST'])
    @login_required
    def create_conversation():
        data = request.get_json()
        conversation_id = str(uuid.uuid4())
        title = data.get('title', 'New Conversation')
        db.add_conversation(session['user_id'], conversation_id, title)
        return jsonify({'conversation_id': conversation_id})
    
    @app.route('/api/chat', methods=['POST'])
    @login_required
    def chat():
        """
        Chat endpoint handling POST requests.
        Expects JSON with 'message' and 'conversation_id'.
        Returns a streaming response.

        Since chat_api.stream_response is asynchronous, we convert its async generator
        into a synchronous generator using a dedicated event loop so that Flask can iterate
        over the tokens and stream the response.
        """
        try:
            data = request.get_json()
            message = data.get('message', '')
            conversation_id = data.get('conversation_id', 'default')
            user_id = session['user_id']

            if not message:
                return Response(
                    f"data: {json.dumps({'error': 'Message is required', 'continuing': False})}\n\n",
                    mimetype='text/event-stream'
                )
            
            #  Get relevant context using RAG
            retrieved_context = query_rag(message) or "" 
            if retrieved_context:
                message = f"Context: {retrieved_context}\n\nUser: {message}"
            
            def sync_stream():
                """
                Synchronously stream tokens by consuming the async generator returned
                by chat_api.stream_response.
                """
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
            logger.error(f"Error in chat endpoint: {e}")
            return Response(
                f"data: {json.dumps({'error': str(e), 'continuing': False})}\n\n",
                mimetype='text/event-stream'
            )

    @app.route('/api/conversations/<conversation_id>/history', methods=['GET'])
    @login_required
    def get_conversation_history(conversation_id: str):
        try:
            user_id = session['user_id']
            logger.debug(f"Getting history for conversation {conversation_id}, user {user_id}")
            
            # Vérifier d'abord si la conversation appartient à l'utilisateur
            with db.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT COUNT(*) 
                    FROM user_conversations 
                    WHERE user_id = ? AND conversation_id = ?
                ''', (user_id, conversation_id))
                if c.fetchone()[0] == 0:
                    logger.warning(f"User {user_id} tried to access unauthorized conversation {conversation_id}")
                    return jsonify({"error": "Conversation not found"}), 404

            conversation = chat_api.get_conversation(user_id, conversation_id)
            history = conversation.get_history()
            logger.debug(f"Retrieved history: {history}")
            
            return jsonify({
                "history": history,
                "conversation_id": conversation_id
            })
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
    @login_required
    def clear_conversation(conversation_id: str):
        """
        Clear the history of a specific conversation.

        Args:
            conversation_id (str): Conversation identifier

        Returns:
            JSON: Success message
        """
        try:
            conversation = chat_api.get_conversation(conversation_id)
            conversation.clear_history()
            return json.dumps({"message": "Conversation cleared successfully"})
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return json.dumps({"error": str(e)}), 500
    
    @app.route('/api/conversations/<conversation_id>/title', methods=['POST'])
    @login_required
    def generate_conversation_title(conversation_id):
        try:
            data = request.get_json()
            first_message = data.get('first_message', '')
            
            title = chat_api.generate_conversation_title(first_message)
            db.update_conversation_title(conversation_id, title)
            return jsonify({"title": title})

        except Exception as e:
            logger.error(f"Error generating title: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500
