from dataclasses import dataclass, field
from datetime import datetime
from typing import List, AsyncIterator
from langchain_core.messages import HumanMessage, AIMessage
from chatModel import CustomHuggingFaceChatModel
from database import Database
import logging
from query_data import query_rag  # Import the RAG function

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
        """
        try:
            # Store user message
            timestamp = datetime.now()
            user_message = Message(role="user", content=message, timestamp=timestamp)
            self.messages.append(user_message)

            # Fetch relevant context using RAG
            retrieved_context = query_rag(message)

            # Debugging: Log retrieved content
            logger.info(f"🔍 RAG Retrieved Context: {retrieved_context[:500] if retrieved_context else '❌ No relevant context found'}")

            # Prevent chatbot from answering if no relevant document is found
            if not retrieved_context:
                yield "I'm sorry, but I couldn't find relevant information in the provided documents."
                return

            # Extract context and sources separately
            if "**Sources**:" in retrieved_context:
                context_text, sources_text = retrieved_context.split("**Sources**:", 1)
                sources_text = sources_text.strip()
            else:
                context_text, sources_text = retrieved_context, ""

            # Prepare messages with context and sources
            formatted_messages = self._prepare_messages(f"Context: {context_text}", sources_text)

            # Generate response based on retrieved context
            current_response = ""
            async for chunk in self.model._astream(formatted_messages):
                token = chunk.message.content
                if token.strip():
                    current_response += token
                    yield token

            # Ensure sources are included at the end of the response
            if sources_text:
                sources_text_formatted = f"\n\n**Sources:**\n{sources_text}"
                yield sources_text_formatted
                current_response += sources_text_formatted

            # Store assistant response (including sources)
            assistant_msg = Message(role="assistant", content=current_response)
            self.messages.append(assistant_msg)

            self._trim_history()

        except Exception as e:
            logger.error(f"🚨 Conversation error: {e}")
            raise





    def _prepare_messages(self, formatted_message: str, sources_text: str = "") -> List[HumanMessage]:
        """
        Ensure the model uses retrieved context and explicitly includes sources.
        """
        model_messages = []

        # Ensure system prompt is added first
        if self.system_prompt:
            model_messages.append(HumanMessage(content=f"System: {self.system_prompt}"))

        # Ensure retrieved context is injected first
        model_messages.append(HumanMessage(content=formatted_message))

        # If sources are available, explicitly add them to the prompt
        if sources_text.strip():
            model_messages.append(HumanMessage(content=f"Sources: {sources_text}"))

        # Append only the most recent messages to maintain conversation flow
        for msg in self.messages[-self.max_history * 2:]:
            if msg.role == "user":
                model_messages.append(HumanMessage(content=f"User: {msg.content}"))
            else:
                model_messages.append(AIMessage(content=f"Assistant: {msg.content}"))

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