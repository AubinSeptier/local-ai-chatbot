from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage, AIMessage
from dataclasses import dataclass, field
from datetime import datetime
import json
from ChatModel import CustomHuggingFaceChatModel
from typing import AsyncIterator

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
    def __init__(
        self,
        conversation_id: str,
        model: CustomHuggingFaceChatModel,
        max_history: int = 5,
        system_prompt: str = "You are a helpful assistant."
    ):
        """
        Initialize a new conversation.

        Args:
            conversation_id (str): Unique identifier for the conversation
            model (CustomHuggingFaceChatModel): The chat model to use
            max_history (int, optional): Maximum number of message pairs to keep. Defaults to 5.
            system_prompt (str, optional): System prompt to use. Defaults to "You are a helpful assistant."
        """
        self.id = conversation_id
        self.model = model
        self.max_history = max_history
        self.system_prompt = system_prompt
        self.messages: List[Message] = []
        
    async def send_message(self, message: str) -> AsyncIterator[str]:
        """
        Send a message and get streaming response.

        Args:
            message (str): User message

        Yields:
            str: Response tokens from the model
        """
        # Add user message to history
        self.messages.append(Message(role="user", content=message))
        
        # Prepare messages for the model
        model_messages = self._prepare_messages_for_model()
        
        # Get streaming response
        current_response = ""
        async for chunk in self.model.astream(model_messages):
            if chunk.content.strip():
                current_response += chunk.content
                yield chunk.content
        
        # Add assistant's complete response to history
        self.messages.append(Message(role="assistant", content=current_response))
        
        # Trim history if needed
        self._trim_history()

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
        """
        Get conversation history in a format suitable for frontend display.

        Returns:
            List[Dict]: List of messages with role and content
        """
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]
    
