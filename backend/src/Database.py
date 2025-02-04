import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file="chat_app.db"):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            c = conn.cursor()
            
            c.execute('PRAGMA foreign_keys = ON')

            # Table des utilisateurs
            c.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL)''')

            # Table des conversations
            c.execute('''CREATE TABLE IF NOT EXISTS user_conversations
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        conversation_id TEXT UNIQUE NOT NULL,
                        title TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id))''')
            
            # Table des messages
            c.execute('''
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES user_conversations(conversation_id)
                )
            ''')

            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                ON conversation_messages(conversation_id)
            ''')
            
            conn.commit()

    def save_message(self, conversation_id: str, role: str, content: str, timestamp: str):
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    INSERT INTO conversation_messages 
                    (conversation_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (conversation_id, role, content, timestamp))
                conn.commit()
                logger.debug(f"Saved message for conversation {conversation_id}: role={role}, content={content[:50]}...")
        except Exception as e:
            logger.error(f"Error saving message: {e}", exc_info=True)
            conn.rollback()
            raise

    def add_user(self, username, password):
        password_hash = generate_password_hash(password)
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                         (username, password_hash))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username, password):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
            result = c.fetchone()
            if result and check_password_hash(result[1], password):
                return result[0]
            return None

    def get_user_conversations(self, user_id):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT conversation_id, title, created_at 
                FROM user_conversations 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            conversations = c.fetchall()
            # Transformons les tuples en dictionnaires avec les bonnes clés
            return [
                {
                    'id': conversation_id,  # Utilisation directe des valeurs du tuple
                    'title': title if title else 'New Conversation',
                    'created_at': created_at
                }
                for conversation_id, title, created_at in conversations
            ]
        
    def add_conversation(self, user_id, conversation_id, title):
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO user_conversations (user_id, conversation_id, title)
                        VALUES (?, ?, ?)''', (user_id, conversation_id, title))
            conn.commit()
    
    def update_conversation_title(self, conversation_id: str, title: str):
        """Update the title of a conversation."""
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('''UPDATE user_conversations 
                        SET title = ?
                        WHERE conversation_id = ?''',
                    (title, conversation_id))
            conn.commit()
    
    def get_conversation_title(self, conversation_id: str) -> str:
        with self.get_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT title FROM user_conversations WHERE conversation_id = ?', (conversation_id,))
            result = c.fetchone()
            return result[0] if result else None
    
    def get_conversation_messages(self, conversation_id: str):
        try:
            with self.get_connection() as conn:
                c = conn.cursor()
                c.execute('''
                    SELECT role, content, timestamp
                    FROM conversation_messages
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                ''', (conversation_id,))
                messages = c.fetchall()
                logger.debug(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
                return messages
        except Exception as e:
            logger.error(f"Error retrieving messages: {e}", exc_info=True)
            return []