from dataclasses import dataclass, field
from datetime import datetime
from typing import List, AsyncIterator
from langchain_core.messages import HumanMessage, AIMessage
from ChatModel import CustomHuggingFaceChatModel
from Database import Database
import logging

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """
    Represents a chat message with metadata.
    
    Attributes:
        role: Message author role (user/assistant)
        content: Message text content
        timestamp: Creation timestamp
    """
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Serialize message to dictionary format."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """Create Message instance from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )

class Conversation:
    """
    Manages a conversation session with history persistence.
    
    Attributes:
        id: Unique conversation ID
        model: Reference to chat model
        max_history: Maximum stored message pairs
        system_prompt: Initial system instruction
        messages: List of conversation messages
        db: Database connection instance
    """
    
    def __init__(
        self,
        conversation_id: str,
        model: CustomHuggingFaceChatModel,
        max_history: int = 5,
        system_prompt: str = "You are a helpful assistant.",
        db: Database = None
    ):
        self.id = conversation_id
        self.model = model
        self.max_history = max_history
        self.system_prompt = system_prompt
        self.db = db or Database()
        self.messages = []
        self._load_messages()

    async def send_message(self, message: str) -> AsyncIterator[str]:
        """
        Process user message and stream assistant response.
        
        Args:
            message: User input text
            
        Yields:
            str: Response tokens as they're generated
        """
        try:
            # Add user message
            user_msg = Message(role="user", content=message)
            self.messages.append(user_msg)

            # Generate and stream response
            current_response = ""
            async for chunk in self.model._astream(self._prepare_messages()):
                token = chunk.message.content
                if token.strip():
                    current_response += token
                    yield token

            # Add assistant response
            assistant_msg = Message(role="assistant", content=current_response)
            self.messages.append(assistant_msg)
            self._trim_history()

        except Exception as e:
            logger.error(f"Conversation error: {e}")
            raise

    def _prepare_messages(self) -> List[HumanMessage]:
        """Format messages for model input including system prompt."""
        model_messages = []
        if self.system_prompt:
            model_messages.append(HumanMessage(content=f"System: {self.system_prompt}"))
        
        for msg in self.messages[-self.max_history * 2:]:
            if msg.role == "user":
                model_messages.append(HumanMessage(content=msg.content))
            else:
                model_messages.append(AIMessage(content=msg.content))
                
        return model_messages

    def _trim_history(self):
        """Keep only recent messages up to max_history limit."""
        if len(self.messages) > self.max_history * 2:
            self.messages = self.messages[-self.max_history * 2:]

    def get_history(self) -> List[dict]:
        """Retrieve formatted conversation history from database."""
        try:
            return [
                {"text": content, "isUser": role == "user", "timestamp": timestamp}
                for role, content, timestamp in self.db.get_conversation_messages(self.id)
            ]
        except Exception as e:
            logger.error(f"History load failed: {e}")
            return []

    def _load_messages(self):
        """Initialize messages from database storage."""
        try:
            self.messages = [
                Message(role=role, content=content, timestamp=datetime.fromisoformat(timestamp))
                for role, content, timestamp in self.db.get_conversation_messages(self.id)
            ]
        except Exception as e:
            logger.error(f"Message load failed: {e}")
            self.messages = []
    
    def add_message(self, role: str, content: str):
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        return msg
