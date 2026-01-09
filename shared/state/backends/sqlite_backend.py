"""
SQLite State Backend for Windows

SQLite-based implementation of StateBackend for Windows systems.
No installation required - SQLite is included with Python.
"""
import sqlite3
import os
import threading
from pathlib import Path
from typing import Dict, Optional
from .base import StateBackend


class SQLiteStateBackend(StateBackend):
    """
    SQLite implementation of StateBackend.

    Uses two tables:
    - kv_store: Simple key-value storage
    - hash_store: Hash-style storage (key -> field -> value)

    Thread-safe with connection pooling per thread.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file. Defaults to ~/Robot/state.db
        """
        if db_path is None:
            db_path = str(Path.home() / 'Robot' / 'state.db')
        elif db_path != ':memory:':
            db_path = os.path.expanduser(db_path)

        self.db_path = db_path
        self._local = threading.local()
        self._init_db()
        print(f"[SQLITE-BACKEND] ✅ Inicializado: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            # Crear directorio si no existe
            if self.db_path != ':memory:':
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            # Optimizaciones de rendimiento
            self._local.conn.execute('PRAGMA journal_mode=WAL')
            self._local.conn.execute('PRAGMA synchronous=NORMAL')
            self._local.conn.execute('PRAGMA temp_store=MEMORY')

        return self._local.conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Tabla para key-value simple
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kv_store (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla para hash storage (Redis-style hashes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hash_store (
                key TEXT,
                field TEXT,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (key, field)
            )
        ''')

        # Índices para mejorar rendimiento
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hash_key ON hash_store(key)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_kv_key ON kv_store(key)
        ''')

        conn.commit()

    def hset(self, key: str, mapping: dict) -> int:
        """Set multiple fields in a hash."""
        conn = self._get_connection()
        cursor = conn.cursor()

        count = 0
        for field, value in mapping.items():
            cursor.execute('''
                INSERT OR REPLACE INTO hash_store (key, field, value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, field, str(value)))
            count += 1

        conn.commit()
        return count

    def hgetall(self, key: str) -> dict:
        """Get all fields and values from a hash."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT field, value FROM hash_store WHERE key = ?
        ''', (key,))

        return {row[0]: row[1] for row in cursor.fetchall()}

    def hget(self, key: str, field: str) -> Optional[str]:
        """Get a single field value from a hash."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT value FROM hash_store WHERE key = ? AND field = ?
        ''', (key, field))

        row = cursor.fetchone()
        return row[0] if row else None

    def set(self, key: str, value: str) -> bool:
        """Set a key-value pair."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO kv_store (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, str(value)))

        conn.commit()
        return True

    def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT value FROM kv_store WHERE key = ?
        ''', (key,))

        row = cursor.fetchone()
        return row[0] if row else None

    def delete(self, key: str) -> int:
        """Delete a key and all its data."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Delete from both tables
        cursor.execute('DELETE FROM kv_store WHERE key = ?', (key,))
        count_kv = cursor.rowcount

        cursor.execute('DELETE FROM hash_store WHERE key = ?', (key,))
        count_hash = cursor.rowcount

        conn.commit()
        return count_kv + count_hash

    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check in kv_store
        cursor.execute('SELECT 1 FROM kv_store WHERE key = ? LIMIT 1', (key,))
        if cursor.fetchone():
            return True

        # Check in hash_store
        cursor.execute('SELECT 1 FROM hash_store WHERE key = ? LIMIT 1', (key,))
        return cursor.fetchone() is not None

    def keys(self, pattern: str = '*') -> list:
        """
        Get all keys matching a pattern.

        Note: SQLite doesn't have Redis-style pattern matching,
        so this uses SQL LIKE with % wildcards.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Convert Redis-style pattern to SQL LIKE pattern
        sql_pattern = pattern.replace('*', '%').replace('?', '_')

        # Get keys from both tables
        keys_set = set()

        cursor.execute('SELECT key FROM kv_store WHERE key LIKE ?', (sql_pattern,))
        keys_set.update(row[0] for row in cursor.fetchall())

        cursor.execute('SELECT DISTINCT key FROM hash_store WHERE key LIKE ?', (sql_pattern,))
        keys_set.update(row[0] for row in cursor.fetchall())

        return list(keys_set)

    def ping(self) -> bool:
        """Test connectivity to the backend."""
        try:
            conn = self._get_connection()
            conn.execute('SELECT 1')
            return True
        except Exception as e:
            print(f"[SQLITE-BACKEND] ❌ Ping failed: {e}")
            return False

    def close(self):
        """Close connections and cleanup resources."""
        if hasattr(self._local, 'conn') and self._local.conn:
            try:
                self._local.conn.close()
                self._local.conn = None
                print(f"[SQLITE-BACKEND] 🔌 Connection closed")
            except Exception as e:
                print(f"[SQLITE-BACKEND] ⚠️  Error closing connection: {e}")

    def vacuum(self):
        """Optimize database (reclaim space, rebuild indices)."""
        conn = self._get_connection()
        conn.execute('VACUUM')
        print(f"[SQLITE-BACKEND] 🧹 Database vacuumed")

    def get_stats(self) -> dict:
        """Get statistics about the database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Count keys in kv_store
        cursor.execute('SELECT COUNT(*) FROM kv_store')
        stats['kv_keys'] = cursor.fetchone()[0]

        # Count unique keys in hash_store
        cursor.execute('SELECT COUNT(DISTINCT key) FROM hash_store')
        stats['hash_keys'] = cursor.fetchone()[0]

        # Total fields in hash_store
        cursor.execute('SELECT COUNT(*) FROM hash_store')
        stats['hash_fields'] = cursor.fetchone()[0]

        # Database size (if not in-memory)
        if self.db_path != ':memory:' and os.path.exists(self.db_path):
            stats['db_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)

        return stats
