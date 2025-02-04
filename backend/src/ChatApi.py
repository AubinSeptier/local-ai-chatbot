import json
import os
from typing import Optional, Dict, List
from ModelManager import ModelManager
from Conversation import Conversation
from ChatModel import CustomHuggingFaceChatModel
import logging
from datetime import datetime
import uuid
from Database import Database
from langchain.schema import HumanMessage
from Conversation import Message

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
        system_prompt: str = "You are a helpful assistant.",
        db = None
    ):
        self.model_manager = ModelManager()
        self.user_conversations = {}  # {user_id: {conversation_id: Conversation}}
        # self.conversations: Dict[str, Conversation] = {}
        self.max_history = max_history
        self.system_prompt = system_prompt
        if db is None:
            self.db = Database()
        else:
            self.db = db

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

    # def save_conversations(self, directory_path: str):
    #     """
    #     Save all conversations to a directory.

    #     Args:
    #         directory_path (str): Directory where conversations will be saved
    #     """
    #     try:
    #         os.makedirs(directory_path, exist_ok=True)

    #         index_data = {
    #             "last_saved": datetime.now().isoformat(),
    #             "conversations": {}
    #         }

    #         for conv_id, conversation in self.conversations.items():
    #             filename = f"conversation_{conv_id}.json"
    #             filepath = os.path.join(directory_path, filename)

    #             conversation.save_history(filepath)

    #             index_data["conversations"][conv_id] = {
    #                 "filename": filename,
    #                 "last_message": conversation.messages[-1].timestamp.isoformat() if conversation.messages else None,
    #                 "message_count": len(conversation.messages)
    #             }

    #         with open(os.path.join(directory_path, "conversations_index.json"), 'w') as f:
    #             json.dump(index_data, f, indent=2)

    #         logger.info(f"Successfully saved {len(self.conversations)} conversations to {directory_path}")
    #         return True

    #     except Exception as e:
    #         logger.error(f"Error saving conversations: {e}")
    #         raise

    # def load_conversations(self, directory_path: str):
    #     """
    #     Load all conversations from a directory.

    #     Args:
    #         directory_path (str): Directory containing saved conversations
    #     """
    #     try:
    #         if not os.path.exists(directory_path):
    #             raise FileNotFoundError(f"Directory {directory_path} does not exist")

    #         index_path = os.path.join(directory_path, "conversations_index.json")
    #         if not os.path.exists(index_path):
    #             raise FileNotFoundError(f"Conversations index not found in {directory_path}")

    #         with open(index_path, 'r') as f:
    #             index_data = json.load(f)

    #         self.conversations.clear()

    #         for conv_id, metadata in index_data["conversations"].items():
    #             filepath = os.path.join(directory_path, metadata["filename"])
    #             if os.path.exists(filepath):
    #                 conversation = Conversation.load_history(
    #                     filepath,
    #                     model=self.chat_model
    #                 )
    #                 self.conversations[conv_id] = conversation
    #             else:
    #                 logger.warning(f"Conversation file {filepath} not found")

    #         logger.info(f"Successfully loaded {len(self.conversations)} conversations from {directory_path}")
    #         return True

    #     except Exception as e:
    #         logger.error(f"Error loading conversations: {e}")
    #         raise

    def get_conversation(self, user_id: str, conversation_id: str) -> Conversation:
        try:
            if user_id not in self.user_conversations:
                self.user_conversations[user_id] = {}
            
            if conversation_id not in self.user_conversations[user_id]:
                logger.debug(f"Creating new conversation object for user {user_id}, conversation {conversation_id}")
                
                # Vérifier si la conversation existe dans la base
                existing_title = self.db.get_conversation_title(conversation_id)
                if existing_title is None:
                    # Créer l'entrée dans user_conversations
                    self.db.add_conversation(user_id, conversation_id, "New Conversation")
                
                # Créer l'instance Conversation
                self.user_conversations[user_id][conversation_id] = Conversation(
                    conversation_id=conversation_id,
                    model=self.chat_model,
                    max_history=self.max_history,
                    system_prompt=self.system_prompt,
                    db=self.db
                )
            
            return self.user_conversations[user_id][conversation_id]
        except Exception as e:
            logger.error(f"Error in get_conversation: {str(e)}")
            raise

    def create_new_conversation(self, user_id: str) -> str:
        """Create a new conversation for a user and return its ID."""
        conversation_id = str(uuid.uuid4())
        self.get_conversation(user_id, conversation_id)
        return conversation_id

    def get_user_conversations(self, user_id: str) -> List[str]:
        """Get all conversation IDs for a user."""
        return list(self.user_conversations.get(user_id, {}).keys())
    
    async def stream_response(self, message: str, user_id: str, conversation_id: str):
        """
        Generate a streaming response for a given message.

        Args:
            message (str): User message
            user_id (str): User identifier
            conversation_id (str): Conversation identifier

        Yields:
            str: SSE formatted response chunks
        """
        try:
            conversation = self.get_conversation(user_id, conversation_id)
            is_first_message = len(conversation.get_history()) == 0

            user_msg = Message(role="user", content=message)
            conversation.messages.append(user_msg)
            self.db.save_message(conversation_id, "user", message, user_msg.timestamp.isoformat())

            current_response = ""
            async for chunk in conversation.send_message(message):
                if chunk.strip():
                    current_response += chunk
                    yield f"data: {json.dumps({'token': chunk, 'continuing': True})}\n\n"
            
            self.db.save_message(conversation_id, "assistant", current_response, user_msg.timestamp.isoformat())

            if is_first_message:
                title = self.generate_conversation_title(message)
                self.db.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'title': title, 'continuing': True})}\n\n"

            yield f"data: {json.dumps({'continuing': False})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in stream_response: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e), 'continuing': False})}\n\n"

    def save_user_conversations(self, user_id: str, directory_path: str):
        """Save all conversations for a user."""
        if user_id not in self.user_conversations:
            return
        
        user_dir = os.path.join(directory_path, f"user_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        
        for conv_id, conversation in self.user_conversations[user_id].items():
            filepath = os.path.join(user_dir, f"conversation_{conv_id}.json")
            conversation.save_history(filepath)

    def load_user_conversations(self, user_id: str, directory_path: str):
        """Load all conversations for a user."""
        user_dir = os.path.join(directory_path, f"user_{user_id}")
        if not os.path.exists(user_dir):
            return
        
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = {}
        
        for filename in os.listdir(user_dir):
            if filename.startswith("conversation_") and filename.endswith(".json"):
                filepath = os.path.join(user_dir, filename)
                conversation = Conversation.load_history(filepath, self.chat_model)
                self.user_conversations[user_id][conversation.id] = conversation

    def generate_conversation_title(self, first_message: str) -> str:
        try:
            # Formatage correct avec le tokenizer
            messages = [{"role": "user", "content": f"Generate a very short title (max 5 words) for this conversation based on this first message: '{first_message}'. Reply with ONLY the title, nothing else."}]
            formatted_prompt = self.chat_model.pipeline.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            response = self.chat_model.pipeline(formatted_prompt)
            title = response[0]['generated_text'].replace(formatted_prompt, '').strip()
            title = title.strip('"\'".,;:')[:50]  # Nettoyage
            logger.debug(f"Generated title: {title}")
            return title
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return "New Conversation"