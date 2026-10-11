"""Database Connection & Schema Manager Module.

Manages SQLite database connections, schema migrations, foreign keys, and transactions.
Satisfies Section 3.2 persistence requirements.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Optional

from library.context_managers import DatabaseTransaction
from library.exceptions import PersistenceError

logger = logging.getLogger("library.database")

SCHEMA_DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS books (
    isbn TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    genre TEXT NOT NULL,
    total_copies INTEGER NOT NULL CHECK(total_copies >= 1),
    available_copies INTEGER NOT NULL CHECK(available_copies >= 0)
);

CREATE TABLE IF NOT EXISTS members (
    member_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    member_type TEXT NOT NULL,
    borrow_limit INTEGER NOT NULL CHECK(borrow_limit >= 1)
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id TEXT PRIMARY KEY,
    isbn TEXT NOT NULL,
    member_id TEXT NOT NULL,
    borrow_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    return_date TEXT,
    fine_amount REAL NOT NULL DEFAULT 0.0,
    fine_paid INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (isbn) REFERENCES books (isbn) ON DELETE RESTRICT,
    FOREIGN KEY (member_id) REFERENCES members (member_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_books_genre ON books (genre);
CREATE INDEX IF NOT EXISTS idx_loans_member_active ON loans (member_id, return_date);
CREATE INDEX IF NOT EXISTS idx_loans_isbn_active ON loans (isbn, return_date);
"""


class DatabaseManager:
    """Manages SQLite database lifecycle, schema initialization, and transactions."""

    def __init__(self, db_path: str = "library.db") -> None:
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Obtain or establish a persistent connection with row factory configured."""
        if self._connection is None:
            if self.db_path != ":memory:":
                parent = Path(self.db_path).parent
                if parent and not parent.exists():
                    parent.mkdir(parents=True, exist_ok=True)

            try:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON;")
                self._connection = conn
            except sqlite3.Error as exc:
                raise PersistenceError(f"Failed to connect to database at '{self.db_path}': {exc}")

        return self._connection

    def _initialize_schema(self) -> None:
        """Execute DDL statements to ensure all tables and indexes exist."""
        conn = self.get_connection()
        try:
            with conn:
                conn.executescript(SCHEMA_DDL)
            logger.info("DATABASE_READY | Schema initialized for '%s'", self.db_path)
        except sqlite3.Error as exc:
            raise PersistenceError(f"Failed to initialize schema: {exc}")

    def transaction(self) -> DatabaseTransaction:
        """Create a custom transaction context manager for atomic units of work."""
        return DatabaseTransaction(self.get_connection())

    def close(self) -> None:
        """Safely close open connection."""
        if self._connection:
            try:
                self._connection.close()
            except sqlite3.Error:
                pass
            self._connection = None
