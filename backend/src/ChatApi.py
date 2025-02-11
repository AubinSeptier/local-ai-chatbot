import json
import uuid
import logging
from datetime import datetime
from typing import Dict

from conversation import Conversation
from modelManager import ModelManager
from chatModel import CustomHuggingFaceChatModel
from database import Database

logger = logging.getLogger(__name__)

class ChatAPI:
    """
    Core chat API handler managing conversations and model interactions.
    
    Attributes:
        model_manager: Handles model loading and configuration
        user_conversations: Dictionary tracking user conversations
        max_history: Maximum conversation history length
        system_prompt: Default system prompt for conversations
        db: Database connection instance
        chat_model: Custom chat model interface
    """
    
    def __init__(
        self,
        model_name: str,
        generation_config: Dict,
        max_history: int,
        system_prompt: str,
        db: Database
    ):
        self.model_manager = ModelManager()
        self.user_conversations: Dict[str, Dict[str, Conversation]] = {}
        self.max_history = max_history
        self.system_prompt = system_prompt
        self.db = db

        # Initialize model pipeline
        pipeline = self.model_manager.load_model(
            model_name,
            generation_config=generation_config
        )
        self.chat_model = CustomHuggingFaceChatModel(pipeline=pipeline)

    def get_conversation(self, user_id: str, conversation_id: str) -> Conversation:
        """
        Retrieve or create a conversation for a user.
        
        Args:
            user_id: Unique user identifier
            conversation_id: Conversation identifier
            
        Returns:
            Conversation: Requested conversation instance
        """
        try:
            if user_id not in self.user_conversations:
                self.user_conversations[user_id] = {}
            
            if conversation_id not in self.user_conversations[user_id]:
                # Create new conversation if not exists
                if not self.db.get_conversation_title(conversation_id):
                    self.db.add_conversation(user_id, conversation_id, "New Conversation")
                
                self.user_conversations[user_id][conversation_id] = Conversation(
                    conversation_id=conversation_id,
                    model=self.chat_model,
                    max_history=self.max_history,
                    system_prompt=self.system_prompt,
                    db=self.db
                )
            
            return self.user_conversations[user_id][conversation_id]
        except Exception as e:
            logger.error(f"Error retrieving conversation: {str(e)}")
            raise

    def create_new_conversation(self, user_id: str) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        self.get_conversation(user_id, conversation_id)
        return conversation_id

    async def stream_response(self, message: str, user_id: str, conversation_id: str):
        """
        Stream response from the chat model.
        
        Args:
            message: User input message
            user_id: User identifier
            conversation_id: Conversation identifier
            
        Yields:
            str: SSE formatted response chunks
        """
        try:
            conversation = self.get_conversation(user_id, conversation_id)
            is_first_message = not conversation.get_history()

            # Save user message
            user_msg = conversation.add_message("user", message)
            self.db.save_message(conversation_id, "user", message, user_msg.timestamp.isoformat())

            # Stream response
            current_response = ""
            async for chunk in conversation.send_message(message):
                if chunk.strip():
                    current_response += chunk
                    yield f"data: {json.dumps({'token': chunk, 'continuing': True})}\n\n"
            
            # Save assistant response
            self.db.save_message(conversation_id, "assistant", current_response, datetime.now().isoformat())

            # Generate title for first message
            if is_first_message:
                title = self.generate_conversation_title(message)
                self.db.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'title': title, 'continuing': True})}\n\n"

            yield f"data: {json.dumps({'continuing': False})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e), 'continuing': False})}\n\n"

    def generate_conversation_title(self, first_message: str) -> str:
        """Generate a conversation title from the first message."""
        try:
            messages = [{
                "role": "user", 
                "content": f"Generate a short title (max 5 words) for: '{first_message}'. Reply with only the title."
            }]
            formatted_prompt = self.chat_model.pipeline.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            response = self.chat_model.pipeline(formatted_prompt)
            title = response[0]['generated_text'].replace(formatted_prompt, '').strip()
            return title.strip('"\'".,;:')[:50]
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return "New Conversation"
