# core/database.py
import sqlite3
import json
import hashlib

def hash_password(password: str) -> str:
    """Securely hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

class DreamDatabase:
    def __init__(self, db_name="dreams.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        # 1. Sessions Table
        self.conn.execute('''CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            username TEXT,
            title TEXT,
            messages TEXT,
            analysis TEXT,
            image_paths TEXT,
            confidence_score INTEGER,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # 2. Users Table (NEW)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )''')
        
        # Safe Migration for old sessions
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA table_info(sessions)")
        existing_columns = [col[1] for col in cursor.fetchall()] 
        if "username" not in existing_columns:
            self.conn.execute("ALTER TABLE sessions ADD COLUMN username TEXT DEFAULT 'admin'")
            
        self.conn.commit()

    def register_user(self, username, password):
        """Registers a new user. Returns True if successful, False if username exists."""
        try:
            hashed_pw = hash_password(password)
            self.conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Username already exists (Primary Key violation)
            return False

    def verify_user(self, username, password):
        """Checks if the username and password match a record in the database."""
        # Hardcoded fallback for the original admin account to prevent lockout
        if username == "admin" and password == "morpheus":
            return True
            
        hashed_pw = hash_password(password)
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
        return cursor.fetchone() is not None

    def save_session(self, session_id: str, username: str, title: str, messages: list, analysis: str, image_paths: list, confidence_score: int = 0):
        messages_json = json.dumps(messages)
        paths_json = json.dumps(image_paths)
        
        self.conn.execute('''
            INSERT INTO sessions (session_id, username, title, messages, analysis, image_paths, confidence_score, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(session_id) DO UPDATE SET
                title = excluded.title,
                messages = excluded.messages,
                analysis = excluded.analysis,
                image_paths = excluded.image_paths,
                confidence_score = excluded.confidence_score,
                updated_at = CURRENT_TIMESTAMP
        ''', (session_id, username, title, messages_json, analysis, paths_json, confidence_score))
        self.conn.commit()

    def fetch_sessions(self, username: str, limit: int = 20):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT session_id, title, messages, analysis, image_paths, confidence_score, updated_at
            FROM sessions
            WHERE username = ?
            ORDER BY updated_at DESC
            LIMIT ?
        ''', (username, limit))
        rows = cursor.fetchall()
        sessions = []
        for r in rows:
            sessions.append({
                "session_id": r[0],
                "title": r[1] or "Untitled Session",
                "messages": json.loads(r[2]) if r[2] else [],
                "analysis": r[3] or "",
                "image_paths": json.loads(r[4]) if r[4] else [],
                "confidence_score": r[5] or 0,
                "updated_at": r[6]
            })
        return sessions

    def delete_session(self, session_id: str, username: str):
        self.conn.execute("DELETE FROM sessions WHERE session_id = ? AND username = ?", (session_id, username))
        self.conn.commit()