import sqlite3
from typing import List, Dict
import uuid

class SQLiteMemory:
    def __init__(self, db_path="memory.db", session_id=None):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.session_id = session_id or str(uuid.uuid4())
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_message(self, role: str, content: str):
        self.conn.execute(
            "INSERT INTO conversation (session_id, role, content) VALUES (?, ?, ?)",
            (self.session_id, role, content)
        )
        self.conn.commit()

    def get_history(self) -> List[Dict]:
        cur = self.conn.execute(
            "SELECT role, content FROM conversation WHERE session_id = ? ORDER BY id",
            (self.session_id,)
        )
        return [{"role": row[0], "content": row[1]} for row in cur.fetchall()]

    def clear_history(self):
        self.conn.execute(
            "DELETE FROM conversation WHERE session_id = ?",
            (self.session_id,)
        )
        self.conn.commit()
