from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage, AIMessage
from dataclasses import dataclass, field
from datetime import datetime
import json
from ChatModel import CustomHuggingFaceChatModel
from typing import AsyncIterator
import logging
from Database import Database
from query_data import query_rag  # Import the RAG function


logger = logging.getLogger(__name__)

@dataclass
class Message:
    """
    Represents a single message in the conversation.
    """
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert message to dictionary format."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        """Create message from dictionary format."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )

class Conversation:
    """
    Manages a conversation with history and streaming support.
    Each conversation has a unique ID and maintains its own message history.
    """
    def __init__(self, conversation_id: str, model: CustomHuggingFaceChatModel, max_history: int = 5, system_prompt: str = "You are a helpful assistant.", db = None):
        self.id = conversation_id
        self.model = model
        self.max_history = max_history
        self.system_prompt = system_prompt
        self.messages = []
        if db is None:
            self.db = Database()
        else:
            self.db = db
        self._load_messages()

    async def send_message(self, message: str) -> AsyncIterator[str]:
        try:
            # Message utilisateur
            timestamp = datetime.now()
            user_message = Message(role="user", content=message, timestamp=timestamp)
            self.messages.append(user_message)  # Garder l'ajout en mémoire
            # SUPPRIMER la ligne de sauvegarde ici
            # Here wwe fetch relevant context using RAG
            retrieved_context = query_rag(message)
            if retrieved_context:
                message = f"Context: {retrieved_context}\n\nUser: {message}"
            else:
                message = f"User: {message}"


            # Génération de la réponse
            current_response = ""
            async for chunk in self.model._astream(self._prepare_messages_for_model()):
                chunk_content = chunk.message.content
                if chunk_content and chunk_content.strip():
                    current_response += chunk_content
                    yield chunk_content

            # Message assistant
            timestamp = datetime.now()
            assistant_message = Message(role="assistant", content=current_response, timestamp=timestamp)
            self.messages.append(assistant_message)  # Garder l'ajout en mémoire
            # SUPPRIMER la ligne de sauvegarde ici

        except Exception as e:
            logger.error(f"Error in send_message: {e}", exc_info=True)
            raise

    def _prepare_messages_for_model(self) -> List:
        """
        Prepare messages in the format expected by the model.
        """
        model_messages = []
        if self.system_prompt:
            model_messages.append(HumanMessage(content=f"System: {self.system_prompt}"))
        
        for msg in self.messages[-self.max_history * 2:]:  # Only use last max_history pairs
            if msg.role == "user":
                model_messages.append(HumanMessage(content=msg.content))
            else:
                model_messages.append(AIMessage(content=msg.content))
        
        return model_messages

    def _trim_history(self):
        """
        Trim history to maximum length.
        """
        if len(self.messages) > self.max_history * 2:  # *2 because we count pairs of messages
            self.messages = self.messages[-self.max_history * 2:]

    def save_history(self, file_path: str):
        """
        Save conversation history to a file.

        Args:
            file_path (str): Path to save the history
        """
        history = {
            "id": self.id,
            "system_prompt": self.system_prompt,
            "messages": [msg.to_dict() for msg in self.messages]
        }
        with open(file_path, 'w') as f:
            json.dump(history, f, indent=2)

    @classmethod
    def load_history(cls, file_path: str, model: CustomHuggingFaceChatModel) -> 'Conversation':
        """
        Load conversation history from a file.

        Args:
            file_path (str): Path to load the history from
            model (CustomHuggingFaceChatModel): The chat model to use

        Returns:
            Conversation: A new conversation instance with loaded history
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        conversation = cls(
            conversation_id=data["id"],
            model=model,
            system_prompt=data["system_prompt"]
        )
        conversation.messages = [Message.from_dict(msg) for msg in data["messages"]]
        return conversation

    def clear_history(self):
        """Clear the conversation history."""
        self.messages = []

    def get_history(self) -> List[Dict]:
        """Get conversation history from database."""
        try:
            messages = self.db.get_conversation_messages(self.id)
            return [
                {
                    "text": content,
                    "isUser": role == "user",
                    "timestamp": timestamp
                }
                for role, content, timestamp in messages
            ]
        except Exception as e:
            logger.error(f"Error getting history: {e}", exc_info=True)
            return []
        
    # def _load_messages(self):
    #     """Charge les messages depuis la base de données."""
    #     try:
    #         with self.db.get_connection() as conn:
    #             c = conn.cursor()
    #             c.execute('''
    #                 SELECT role, content, timestamp
    #                 FROM conversation_messages
    #                 WHERE conversation_id = ?
    #                 ORDER BY timestamp ASC
    #             ''', (self.id,))
    #             rows = c.fetchall()
    #             self.messages = []  # Réinitialiser les messages
    #             for row in rows:
    #                 self.messages.append(Message(
    #                     role=row[0],
    #                     content=row[1],
    #                     timestamp=datetime.fromisoformat(row[2]) if row[2] else datetime.now()
    #                 ))
    #             logger.debug(f"Loaded {len(self.messages)} messages for conversation {self.id}")
    #     except Exception as e:
    #         logger.error(f"Error loading messages: {e}", exc_info=True)
    #         self.messages = []

    def _load_messages(self):
        """Charge les messages depuis la base de données."""
        try:
            messages = self.db.get_conversation_messages(self.id)
            self.messages = []
            for role, content, timestamp in messages:
                try:
                    timestamp_dt = datetime.fromisoformat(timestamp) if timestamp else datetime.now()
                    self.messages.append(Message(
                        role=role,
                        content=content,
                        timestamp=timestamp_dt
                    ))
                except Exception as e:
                    logger.error(f"Error parsing message: {e}", exc_info=True)
            logger.debug(f"Loaded {len(self.messages)} messages for conversation {self.id}")
        except Exception as e:
            logger.error(f"Error loading messages: {e}", exc_info=True)
            self.messages = []

    def _save_message(self, message: Message):
        """Sauvegarde un message dans la base de données."""
        try:
            with self.db.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO conversation_messages
                    (conversation_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (self.id, message.role, message.content, message.timestamp.isoformat()))
                conn.commit()
                logger.debug(f"Saved message for conversation {self.id}: {message.content[:50]}...")
        except Exception as e:
            logger.error(f"Error saving message: {e}", exc_info=True)
    
