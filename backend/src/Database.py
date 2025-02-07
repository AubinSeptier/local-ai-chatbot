import sqlite3
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class Database:
    """
    Handles database operations for user authentication and conversation storage.
    
    Attributes:
        db_file (str): Path to the SQLite database file
    """
    
    def __init__(self, db_file: str = "chat_app.db"):
        self.db_file = db_file
        self._initialize_database()

    def get_connection(self) -> sqlite3.Connection:
        """
        Create and return a new database connection with foreign keys enabled.
        
        Returns:
            sqlite3.Connection: Active database connection
        """
        conn = sqlite3.connect(self.db_file)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _initialize_database(self):
        """Create database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )''')

            # Conversations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    conversation_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )''')

            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES user_conversations(conversation_id)
                )''')

            # Index for faster message retrieval
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                ON conversation_messages(conversation_id)
            ''')
            
            conn.commit()

    def save_message(self, conversation_id: str, role: str, content: str, timestamp: str):
        """
        Save a message to the database.
        
        Args:
            conversation_id (str): Unique conversation identifier
            role (str): 'user' or 'assistant'
            content (str): Message content
            timestamp (str): ISO formatted timestamp
        """
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO conversation_messages 
                    (conversation_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (conversation_id, role, content, timestamp))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save message: {str(e)}")
            raise

    def add_user(self, username: str, password: str) -> bool:
        """
        Register a new user.
        
        Args:
            username (str): User's username
            password (str): User's password
            
        Returns:
            bool: True if registration successful, False if username exists
        """
        password_hash = generate_password_hash(password)
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO users (username, password_hash)
                    VALUES (?, ?)
                ''', (username, password_hash))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username: str, password: str) -> Optional[int]:
        """
        Authenticate a user.
        
        Args:
            username (str): User's username
            password (str): User's password
            
        Returns:
            Optional[int]: User ID if authentication successful, None otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, password_hash 
                FROM users 
                WHERE username = ?
            ''', (username,))
            result = cursor.fetchone()
            
            if result and check_password_hash(result[1], password):
                return result[0]
            return None

    def get_user_conversations(self, user_id: int) -> List[Dict]:
        """
        Retrieve all conversations for a user.
        
        Args:
            user_id (int): User's unique identifier
            
        Returns:
            List[Dict]: List of conversation dictionaries with id, title, and created_at
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT conversation_id, title, created_at 
                FROM user_conversations 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            
            return [{
                'id': row[0],
                'title': row[1] or 'New Conversation',
                'created_at': row[2]
            } for row in cursor.fetchall()]

    def add_conversation(self, user_id: int, conversation_id: str, title: str):
        """
        Create a new conversation entry.
        
        Args:
            user_id (int): Owner's user ID
            conversation_id (str): Unique conversation identifier
            title (str): Initial conversation title
        """
        with self.get_connection() as conn:
            conn.execute('''
                INSERT INTO user_conversations (user_id, conversation_id, title)
                VALUES (?, ?, ?)
            ''', (user_id, conversation_id, title))
            conn.commit()

    def update_conversation_title(self, conversation_id: str, title: str):
        """
        Update a conversation's title.
        
        Args:
            conversation_id (str): Conversation identifier
            title (str): New title
        """
        with self.get_connection() as conn:
            conn.execute('''
                UPDATE user_conversations 
                SET title = ?
                WHERE conversation_id = ?
            ''', (title, conversation_id))
            conn.commit()

    def get_conversation_title(self, conversation_id: str) -> Optional[str]:
        """
        Retrieve a conversation's title.
        
        Args:
            conversation_id (str): Conversation identifier
            
        Returns:
            Optional[str]: Conversation title if found, None otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title 
                FROM user_conversations 
                WHERE conversation_id = ?
            ''', (conversation_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def get_conversation_messages(self, conversation_id: str) -> List[Tuple[str, str, str]]:
        """
        Retrieve all messages for a conversation.
        
        Args:
            conversation_id (str): Conversation identifier
            
        Returns:
            List[Tuple]: List of message tuples (role, content, timestamp)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content, timestamp
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
            ''', (conversation_id,))
            return cursor.fetchall()