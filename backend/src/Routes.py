from flask import request, Response, stream_with_context
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

def register_routes(app, chat_api):
    """
    Register all routes for the application.
    """
    
    @app.route('/api/chat', methods=['POST'])
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
            
            if not message:
                return Response(
                    f"data: {json.dumps({'error': 'Message is required', 'continuing': False})}\n\n",
                    mimetype='text/event-stream'
                )
            
            def sync_stream():
                """
                Synchronously stream tokens by consuming the async generator returned
                by chat_api.stream_response.
                """
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                async_gen = chat_api.stream_response(message, conversation_id)
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
    def get_conversation_history(conversation_id: str):
        """
        Get the history of a specific conversation.

        Args:
            conversation_id (str): Conversation identifier

        Returns:
            JSON: Conversation history
        """
        try:
            conversation = chat_api.get_conversation(conversation_id)
            return json.dumps({"history": conversation.get_history()})
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return json.dumps({"error": str(e)}), 500

    @app.route('/api/conversations/<conversation_id>', methods=['DELETE'])
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
