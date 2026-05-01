import re
import sqlite3
import threading
from typing import List, Dict, Optional
import uuid
import hashlib
import json

class HierarchicalMemory:
    """
    分层记忆系统：
    - 短期记忆：最近的对话轮次
    - 长期记忆：基于关键词的简单检索（暂时替代向量搜索）
    - 总结记忆：对话内容的总结
    """

    def __init__(self, db_path="memory.db", session_id=None, recent_limit=10):
        # SQLite for basic storage
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        self.session_id = session_id or str(uuid.uuid4())
        self.recent_limit = recent_limit
        self._create_table()

        # Simple keyword index for long-term memory (替代向量搜索)
        self.keyword_index = {}
        self._rebuild_keyword_index()

        # Summary storage — load persisted value from DB
        self.summary = self._load_summary()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                turn_number INTEGER,
                keywords TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS session_summary (
                session_id TEXT PRIMARY KEY,
                summary TEXT NOT NULL DEFAULT '',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def _rebuild_keyword_index(self) -> None:
        """Rebuild the in-memory keyword index from existing DB rows for this session."""
        cur = self.conn.execute(
            "SELECT role, content, turn_number, keywords FROM conversation WHERE session_id = ?",
            (self.session_id,)
        )
        for role, content, turn_number, keywords_str in cur.fetchall():
            try:
                keywords = json.loads(keywords_str or "[]")
            except Exception:
                keywords = []
            for keyword in keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = []
                self.keyword_index[keyword].append({
                    "turn_number": turn_number,
                    "role": role,
                    "content": content,
                })

    _SHELL_KEYWORDS = {
        'ls', 'cd', 'mkdir', 'rm', 'cp', 'mv', 'cat', 'grep', 'find', 'chmod',
        'chown', 'ps', 'kill', 'top', 'df', 'du', 'tar', 'gzip', 'ssh', 'scp',
        'file', 'size', 'directory', 'folder', 'hidden', 'permission', 'process',
        'curl', 'wget', 'ping', 'netstat', 'awk', 'sed', 'sort', 'uniq', 'wc',
        'head', 'tail', 'echo', 'export', 'source', 'cron', 'systemctl', 'sudo',
    }
    _STOP_WORDS = {
        'this', 'that', 'with', 'from', 'have', 'will', 'been', 'were',
        'they', 'them', 'your', 'what', 'when', 'where', 'which', 'there',
        'their', 'about', 'just', 'also', 'into', 'then', 'than', 'some',
    }

    def _extract_keywords(self, content: str) -> List[str]:
        """关键词提取：优先 shell 命令词，再回退到通用词和中文词。"""
        seen: set = set()
        keywords: List[str] = []
        content_lower = content.lower()

        # Pass 1: shell command words (exact match)
        for kw in self._SHELL_KEYWORDS:
            if kw in content_lower and kw not in seen:
                seen.add(kw)
                keywords.append(kw)

        # Pass 2: general English words (>= 4 chars, not stop-words)
        for w in re.findall(r'\b[a-z]{4,}\b', content_lower):
            if w not in seen and w not in self._STOP_WORDS:
                seen.add(w)
                keywords.append(w)
            if len(keywords) >= 10:
                break

        # Pass 3: Chinese 2-4 char sequences
        for w in re.findall(r'[\u4e00-\u9fff]{2,4}', content):
            if w not in seen:
                seen.add(w)
                keywords.append(w)
            if len(keywords) >= 10:
                break

        return keywords[:10]

    def add_message(self, role: str, content: str):
        # Get current turn number
        cur = self.conn.execute(
            "SELECT MAX(turn_number) FROM conversation WHERE session_id = ?",
            (self.session_id,)
        )
        result = cur.fetchone()
        turn_number = (result[0] or 0) + 1

        # Extract keywords
        keywords = self._extract_keywords(content)
        keywords_str = json.dumps(keywords)

        # Store in SQLite
        with self._lock:
            self.conn.execute(
                "INSERT INTO conversation (session_id, role, content, turn_number, keywords) VALUES (?, ?, ?, ?, ?)",
                (self.session_id, role, content, turn_number, keywords_str)
            )
            self.conn.commit()

        # Update keyword index
        for keyword in keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = []
            self.keyword_index[keyword].append({
                "turn_number": turn_number,
                "role": role,
                "content": content
            })

        # Auto-generate a lightweight summary only when no manual summary is set.
        if not self.summary:
            self._refresh_auto_summary()

    def _load_summary(self) -> str:
        """Load persisted summary from SQLite for this session."""
        cur = self.conn.execute(
            "SELECT summary FROM session_summary WHERE session_id = ?",
            (self.session_id,)
        )
        row = cur.fetchone()
        return row[0] if row else ""

    def _persist_summary(self) -> None:
        """Write current summary to SQLite so it survives object re-creation."""
        with self._lock:
            self.conn.execute(
                "INSERT INTO session_summary (session_id, summary) VALUES (?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET summary=excluded.summary, "
                "updated_at=CURRENT_TIMESTAMP",
                (self.session_id, self.summary)
            )
            self.conn.commit()

    def _refresh_auto_summary(self):
        """Build a concise summary from recent user intents and persist it."""
        recent = self.get_recent_history(limit=6)
        user_messages = [
            m["content"].strip()
            for m in recent
            if m.get("role") == "user" and m.get("content", "").strip()
        ]
        if not user_messages:
            self.summary = ""
            return

        # Summarise as: recent intent list (capped to 240 chars)
        intents = user_messages[-3:]
        self.summary = ("用户近期关注：" + "；".join(intents))[:240]
        self._persist_summary()

    def get_recent_history(self, limit: Optional[int] = None) -> List[Dict]:
        """获取最近的对话历史"""
        limit = limit or self.recent_limit
        cur = self.conn.execute(
            "SELECT role, content FROM conversation WHERE session_id = ? ORDER BY id DESC LIMIT ?",
            (self.session_id, limit * 2)  # *2 because each turn has user + assistant
        )
        rows = cur.fetchall()
        # Reverse to get chronological order
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

    def get_relevant_history(self, query: str, top_k: int = 3) -> List[Dict]:
        """基于关键词匹配检索相关历史"""
        query_keywords = self._extract_keywords(query)
        if not query_keywords:
            return []

        # Find matching messages
        relevant_messages = []
        seen_turns = set()

        for keyword in query_keywords:
            if keyword in self.keyword_index:
                for msg in self.keyword_index[keyword]:
                    turn_key = (msg["turn_number"], msg["role"])
                    if turn_key not in seen_turns:
                        relevant_messages.append({
                            "role": msg["role"],
                            "content": msg["content"],
                            "turn_number": msg["turn_number"]
                        })
                        seen_turns.add(turn_key)

        # Sort by turn number and limit results
        relevant_messages.sort(key=lambda x: x["turn_number"])
        return relevant_messages[-top_k:]  # Get most recent relevant messages

    def update_summary(self, new_summary: str):
        """更新对话总结"""
        self.summary = new_summary
        self._persist_summary()

    def get_memory_context(self, current_input: str) -> Dict[str, str]:
        """获取分层记忆上下文"""
        # 短期记忆：最近几轮
        recent_history = self.get_recent_history()

        # 长期记忆：相关历史片段
        relevant_history = self.get_relevant_history(current_input)

        # 格式化输出
        recent_text = "\n".join([
            f"<{msg['role']}>\n{msg['content']}\n</{msg['role']}>"
            for msg in recent_history
        ])

        relevant_text = "\n".join([
            f"<{msg['role']}>\n{msg['content']}\n</{msg['role']}>"
            for msg in relevant_history
        ])

        return {
            "summary": self.summary,
            "recent_history": recent_text,
            "relevant_memory": relevant_text
        }

    def clear_history(self):
        """清除所有记忆"""
        with self._lock:
            self.conn.execute("DELETE FROM conversation WHERE session_id = ?", (self.session_id,))
            self.conn.execute("DELETE FROM session_summary WHERE session_id = ?", (self.session_id,))
            self.conn.commit()

        # Clear keyword index
        self.keyword_index = {}

        # Clear summary
        self.summary = ""

# 保持向后兼容的别名
SQLiteMemory = HierarchicalMemory