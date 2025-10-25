import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DatabaseSessionService:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.getenv("DATABASE_PATH", "data/sessions.db")
        
        self.db_path = Path(__file__).parent.parent / db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    video_id TEXT,
                    video_url TEXT,
                    feature_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(app_name, user_id, session_id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_pk INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (session_pk) REFERENCES sessions(id) ON DELETE CASCADE,
                    UNIQUE(session_pk, key)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_pk INTEGER NOT NULL,
                    version_number INTEGER NOT NULL,
                    video_url TEXT,
                    state_snapshot TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_pk) REFERENCES sessions(id) ON DELETE CASCADE,
                    UNIQUE(session_pk, version_number)
                )
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def create_session(
        self, 
        app_name: str, 
        user_id: str, 
        session_id: str,
        video_id: Optional[str] = None,
        video_url: Optional[str] = None,
        feature_id: Optional[str] = None
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            cursor.execute("""
                INSERT OR REPLACE INTO sessions 
                (app_name, user_id, session_id, video_id, video_url, feature_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (app_name, user_id, session_id, video_id, video_url, feature_id, now, now))
            
            session_pk = cursor.lastrowid
            if session_pk is None:
                raise ValueError("Failed to create session")
            conn.commit()
            logger.info(f"Session created: {app_name}/{user_id}/{session_id}")
            return session_pk
    
    def get_session(
        self, 
        app_name: str, 
        user_id: str, 
        session_id: str
    ) -> Optional[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, app_name, user_id, session_id, video_id, video_url, 
                       feature_id, created_at, updated_at
                FROM sessions
                WHERE app_name = ? AND user_id = ? AND session_id = ?
            """, (app_name, user_id, session_id))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            session = {
                "pk": row[0],
                "app_name": row[1],
                "user_id": row[2],
                "session_id": row[3],
                "video_id": row[4],
                "video_url": row[5],
                "feature_id": row[6],
                "created_at": row[7],
                "updated_at": row[8],
                "state": {}
            }
            
            cursor.execute("""
                SELECT key, value
                FROM session_state
                WHERE session_pk = ?
            """, (session["pk"],))
            
            for key, value in cursor.fetchall():
                try:
                    session["state"][key] = json.loads(value)
                except json.JSONDecodeError:
                    session["state"][key] = value
            
            return session
    
    def list_sessions(
        self,
        user_id: str,
        video_id: Optional[str] = None,
        feature_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT id, app_name, user_id, session_id, video_id, video_url, 
                       feature_id, created_at, updated_at
                FROM sessions
                WHERE user_id = ?
            """
            params = [user_id]
            
            if video_id:
                query += " AND video_id = ?"
                params.append(video_id)
            
            if feature_id:
                query += " AND feature_id = ?"
                params.append(feature_id)
            
            query += " ORDER BY updated_at DESC"
            
            cursor.execute(query, params)
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    "pk": row[0],
                    "app_name": row[1],
                    "user_id": row[2],
                    "session_id": row[3],
                    "video_id": row[4],
                    "video_url": row[5],
                    "feature_id": row[6],
                    "created_at": row[7],
                    "updated_at": row[8]
                })
            
            return sessions
    
    def set_state(
        self, 
        session_pk: int, 
        key: str, 
        value: Any
    ):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            value_json = json.dumps(value) if not isinstance(value, str) else value
            
            cursor.execute("""
                INSERT OR REPLACE INTO session_state (session_pk, key, value, updated_at)
                VALUES (?, ?, ?, ?)
            """, (session_pk, key, value_json, now))
            
            cursor.execute("""
                UPDATE sessions SET updated_at = ? WHERE id = ?
            """, (now, session_pk))
            
            conn.commit()
    
    def get_state(
        self, 
        session_pk: int, 
        key: str
    ) -> Optional[Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value FROM session_state
                WHERE session_pk = ? AND key = ?
            """, (session_pk, key))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return row[0]
    
    def clear_state(self, session_pk: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM session_state WHERE session_pk = ?
            """, (session_pk,))
            conn.commit()
            logger.info(f"Cleared state for session_pk={session_pk}")
    
    def create_version(
        self,
        session_pk: int,
        video_url: Optional[str] = None
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            cursor.execute("""
                SELECT COALESCE(MAX(version_number), 0) FROM session_versions
                WHERE session_pk = ?
            """, (session_pk,))
            next_version = cursor.fetchone()[0] + 1
            
            cursor.execute("""
                SELECT key, value FROM session_state WHERE session_pk = ?
            """, (session_pk,))
            state_snapshot = json.dumps(dict(cursor.fetchall()))
            
            cursor.execute("""
                INSERT INTO session_versions 
                (session_pk, version_number, video_url, state_snapshot, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session_pk, next_version, video_url, state_snapshot, now))
            
            version_id = cursor.lastrowid
            if version_id is None:
                raise ValueError("Failed to create version")
            conn.commit()
            logger.info(f"Created version {next_version} for session_pk={session_pk}")
            return version_id
    
    def get_versions(self, session_pk: int) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, version_number, video_url, created_at
                FROM session_versions
                WHERE session_pk = ?
                ORDER BY version_number DESC
            """, (session_pk,))
            
            versions = []
            for row in cursor.fetchall():
                versions.append({
                    "id": row[0],
                    "version_number": row[1],
                    "video_url": row[2],
                    "created_at": row[3]
                })
            
            return versions
    
    def delete_session(self, app_name: str, user_id: str, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM sessions
                WHERE app_name = ? AND user_id = ? AND session_id = ?
            """, (app_name, user_id, session_id))
            conn.commit()
            logger.info(f"Deleted session: {app_name}/{user_id}/{session_id}")
    
    def delete_all_sessions(self, user_id: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM sessions WHERE user_id = ?
            """, (user_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            logger.info(f"Deleted {deleted_count} sessions for user_id={user_id}")
            return deleted_count


database_session_service = DatabaseSessionService()
