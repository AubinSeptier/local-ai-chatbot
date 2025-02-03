import json
import os
from typing import Optional, Dict, List
from ModelManager import ModelManager
from Conversation import Conversation
from ChatModel import CustomHuggingFaceChatModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatAPI:
    """
    Manages chat functionality and state.
    """
    def __init__(
        self,
        pipeline=None,
        model_name: Optional[str] = None,
        generation_config: Optional[Dict] = None,
        max_history: int = 5,
        system_prompt: str = "You are a helpful assistant."
    ):
        self.model_manager = ModelManager()
        self.conversations: Dict[str, Conversation] = {}
        self.max_history = max_history
        self.system_prompt = system_prompt
        
        if pipeline is not None:
            self.chat_model = CustomHuggingFaceChatModel(pipeline=pipeline)
        elif model_name is not None:
            pipeline = self.model_manager.load_model(
                model_name,
                generation_config=generation_config
            )
            self.chat_model = CustomHuggingFaceChatModel(pipeline=pipeline)
        else:
            raise ValueError("Either pipeline or model_name must be provided")

    def save_conversations(self, directory_path: str):
        """
        Save all conversations to a directory.

        Args:
            directory_path (str): Directory where conversations will be saved
        """
        try:
            os.makedirs(directory_path, exist_ok=True)

            index_data = {
                "last_saved": datetime.now().isoformat(),
                "conversations": {}
            }

            for conv_id, conversation in self.conversations.items():
                filename = f"conversation_{conv_id}.json"
                filepath = os.path.join(directory_path, filename)

                conversation.save_history(filepath)

                index_data["conversations"][conv_id] = {
                    "filename": filename,
                    "last_message": conversation.messages[-1].timestamp.isoformat() if conversation.messages else None,
                    "message_count": len(conversation.messages)
                }

            with open(os.path.join(directory_path, "conversations_index.json"), 'w') as f:
                json.dump(index_data, f, indent=2)

            logger.info(f"Successfully saved {len(self.conversations)} conversations to {directory_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving conversations: {e}")
            raise

    def load_conversations(self, directory_path: str):
        """
        Load all conversations from a directory.

        Args:
            directory_path (str): Directory containing saved conversations
        """
        try:
            if not os.path.exists(directory_path):
                raise FileNotFoundError(f"Directory {directory_path} does not exist")

            index_path = os.path.join(directory_path, "conversations_index.json")
            if not os.path.exists(index_path):
                raise FileNotFoundError(f"Conversations index not found in {directory_path}")

            with open(index_path, 'r') as f:
                index_data = json.load(f)

            self.conversations.clear()

            for conv_id, metadata in index_data["conversations"].items():
                filepath = os.path.join(directory_path, metadata["filename"])
                if os.path.exists(filepath):
                    conversation = Conversation.load_history(
                        filepath,
                        model=self.chat_model
                    )
                    self.conversations[conv_id] = conversation
                else:
                    logger.warning(f"Conversation file {filepath} not found")

            logger.info(f"Successfully loaded {len(self.conversations)} conversations from {directory_path}")
            return True

        except Exception as e:
            logger.error(f"Error loading conversations: {e}")
            raise

    def get_conversation(self, conversation_id: str) -> Conversation:
        """
        Get or create a conversation for the given ID.

        Args:
            conversation_id (str): Unique identifier for the conversation

        Returns:
            Conversation: The conversation instance
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = Conversation(
                conversation_id=conversation_id,
                model=self.chat_model,
                max_history=self.max_history,
                system_prompt=self.system_prompt
            )
        return self.conversations[conversation_id]

    async def stream_response(self, message: str, conversation_id: str):
        """
        Generate a streaming response for a given message.

        Args:
            message (str): User message
            conversation_id (str): Conversation identifier

        Yields:
            str: SSE formatted response chunks
        """
        try:
            conversation = self.get_conversation(conversation_id)
            
            async for chunk in conversation.send_message(message):
                if chunk.strip():
                    yield f"data: {json.dumps({'token': chunk, 'continuing': True})}\n\n"
            
            yield f"data: {json.dumps({'continuing': False})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in stream_response: {e}")
            yield f"data: {json.dumps({'error': str(e), 'continuing': False})}\n\n"