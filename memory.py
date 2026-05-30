"""
memory.py — FoxyAI Long-Term Memory
SQLite-based. Remembers the user forever.
No internet. No cloud. Everything stays on device.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional


DB_PATH = "foxy_memory.db"


# ── Setup ─────────────────────────────────────────────────────────────────────

def init_db(path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS user_profile (
            key     TEXT PRIMARY KEY,
            value   TEXT NOT NULL,
            updated TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            role      TEXT NOT NULL,
            content   TEXT NOT NULL,
            mood      TEXT DEFAULT 'neutral',
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS manga_stories (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            title     TEXT NOT NULL,
            topic     TEXT NOT NULL,
            chapters  TEXT NOT NULL,
            created   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS emotions_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            mood      TEXT NOT NULL,
            trigger   TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS knowledge_cache (
            key       TEXT PRIMARY KEY,
            value     TEXT NOT NULL,
            updated   TEXT NOT NULL
        );
    """)
    conn.commit()


# ── User Profile ──────────────────────────────────────────────────────────────

class UserProfile:
    """Stores and retrieves persistent facts about the user."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def set(self, key: str, value) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO user_profile (key, value, updated) VALUES (?, ?, ?)",
            (key, json.dumps(value), _now())
        )
        self.conn.commit()

    def get(self, key: str, default=None):
        row = self.conn.execute(
            "SELECT value FROM user_profile WHERE key = ?", (key,)
        ).fetchone()
        return json.loads(row["value"]) if row else default

    def get_all(self) -> dict:
        rows = self.conn.execute("SELECT key, value FROM user_profile").fetchall()
        return {r["key"]: json.loads(r["value"]) for r in rows}

    def delete(self, key: str) -> None:
        self.conn.execute("DELETE FROM user_profile WHERE key = ?", (key,))
        self.conn.commit()

    def summary(self) -> str:
        """Returns a natural language summary of what Foxy knows about the user."""
        data = self.get_all()
        if not data:
            return "I don't know much about you yet."

        parts = []
        if "name" in data:
            parts.append(f"Your name is {data['name']}")
        if "age" in data:
            parts.append(f"you're {data['age']} years old")
        if "country" in data:
            parts.append(f"you're from {data['country']}")
        if "language" in data:
            parts.append(f"you speak {data['language']}")
        if "likes" in data:
            parts.append(f"you like {', '.join(data['likes'])}")
        if "dislikes" in data:
            parts.append(f"you dislike {', '.join(data['dislikes'])}")
        if "mood_history" in data:
            parts.append(f"your usual mood is {data['mood_history']}")

        return ". ".join(parts) + "."


# ── Conversation History ──────────────────────────────────────────────────────

class ConversationMemory:
    """Stores full chat history and retrieves recent context."""

    def __init__(self, conn: sqlite3.Connection, max_context: int = 20):
        self.conn = conn
        self.max_context = max_context

    def add(self, role: str, content: str, mood: str = "neutral") -> None:
        self.conn.execute(
            "INSERT INTO messages (role, content, mood, timestamp) VALUES (?, ?, ?, ?)",
            (role, content, mood, _now())
        )
        self.conn.commit()

    def recent(self, n: int = None) -> list[dict]:
        """Get last n messages as list of dicts for LLM context."""
        limit = n or self.max_context
        rows = self.conn.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def total_count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

    def clear(self) -> None:
        self.conn.execute("DELETE FROM messages")
        self.conn.commit()

    def search(self, keyword: str) -> list[dict]:
        """Search past messages for a keyword."""
        rows = self.conn.execute(
            "SELECT role, content, timestamp FROM messages WHERE content LIKE ? ORDER BY id DESC LIMIT 10",
            (f"%{keyword}%",)
        ).fetchall()
        return [dict(r) for r in rows]


# ── Emotion Log ───────────────────────────────────────────────────────────────

class EmotionMemory:
    """Tracks mood history so Foxy understands the user's emotional patterns."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def log(self, mood: str, trigger: str) -> None:
        self.conn.execute(
            "INSERT INTO emotions_log (mood, trigger, timestamp) VALUES (?, ?, ?)",
            (mood, trigger, _now())
        )
        self.conn.commit()

    def dominant_mood(self) -> str:
        """Returns the user's most frequent mood."""
        row = self.conn.execute(
            "SELECT mood, COUNT(*) as count FROM emotions_log GROUP BY mood ORDER BY count DESC LIMIT 1"
        ).fetchone()
        return row["mood"] if row else "neutral"

    def recent_moods(self, n: int = 5) -> list[str]:
        rows = self.conn.execute(
            "SELECT mood FROM emotions_log ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        return [r["mood"] for r in rows]


# ── Manga Story Memory ────────────────────────────────────────────────────────

class MangaMemory:
    """Saves generated manga stories so user can revisit them."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save(self, title: str, topic: str, chapters: list[dict]) -> int:
        cursor = self.conn.execute(
            "INSERT INTO manga_stories (title, topic, chapters, created) VALUES (?, ?, ?, ?)",
            (title, topic, json.dumps(chapters), _now())
        )
        self.conn.commit()
        return cursor.lastrowid

    def get(self, story_id: int) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM manga_stories WHERE id = ?", (story_id,)
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "topic": row["topic"],
            "chapters": json.loads(row["chapters"]),
            "created": row["created"],
        }

    def all_titles(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, title, topic, created FROM manga_stories ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


# ── Main Memory Manager ───────────────────────────────────────────────────────

class FoxyMemory:
    """
    Single entry point for all memory systems.
    Import this in brain.py and everywhere else.

    Usage:
        mem = FoxyMemory()
        mem.profile.set("name", "Alex")
        mem.chat.add("user", "hello foxy")
        mem.emotion.log("happy", "user said something funny")
    """

    def __init__(self, db_path: str = DB_PATH):
        self.conn = init_db(db_path)
        self.profile  = UserProfile(self.conn)
        self.chat     = ConversationMemory(self.conn)
        self.emotion  = EmotionMemory(self.conn)
        self.manga    = MangaMemory(self.conn)

    def build_context_prompt(self) -> str:
        """
        Builds a rich context string to inject into every LLM prompt.
        Tells Foxy everything she knows about the user.
        """
        profile_summary = self.profile.summary()
        dominant_mood   = self.emotion.dominant_mood()
        total_messages  = self.chat.total_count()
        name            = self.profile.get("name", "friend")

        bond_level = (
            "best friends" if total_messages > 500
            else "close friends" if total_messages > 100
            else "getting to know each other" if total_messages > 20
            else "just met"
        )

        return (
            f"User info: {profile_summary} "
            f"Bond level: {bond_level} ({total_messages} messages exchanged). "
            f"Their usual mood is: {dominant_mood}. "
            f"Call them '{name}' naturally in conversation."
        )

    def extract_and_save_user_facts(self, text: str) -> None:
        """
        Simple rule-based fact extraction from user messages.
        Saves name, age, country, likes automatically.
        """
        t = text.lower()

        # Name detection
        for phrase in ["my name is ", "i'm ", "i am ", "call me "]:
            if phrase in t:
                idx = t.index(phrase) + len(phrase)
                name = text[idx:].split()[0].strip(".,!?")
                if len(name) > 1:
                    self.profile.set("name", name.capitalize())
                    break

        # Age detection
        import re
        age_match = re.search(r"i(?:'m| am) (\d{1,2})(?: years old)?", t)
        if age_match:
            self.profile.set("age", int(age_match.group(1)))

        # Country detection
        for phrase in ["i'm from ", "i am from ", "i live in "]:
            if phrase in t:
                idx = t.index(phrase) + len(phrase)
                country = text[idx:].split()[0].strip(".,!?")
                if len(country) > 1:
                    self.profile.set("country", country.capitalize())
                    break

        # Likes detection
        if "i like " in t or "i love " in t:
            phrase = "i like " if "i like " in t else "i love "
            idx = t.index(phrase) + len(phrase)
            thing = text[idx:].split(".")[0].strip(".,!?")
            likes = self.profile.get("likes", [])
            if thing and thing not in likes:
                likes.append(thing)
                self.profile.set("likes", likes[-10:])  # keep last 10

    def close(self) -> None:
        self.conn.close()


# ── Utility ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
