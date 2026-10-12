"""Custom Context Managers Module.

Implements custom context managers conforming to Section 3.2 requirements.
Wraps persistence transactions to ensure atomic commits and automatic rollbacks
on domain or system failures.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from types import TracebackType
from typing import Generator, Optional, Type

logger = logging.getLogger("library.persistence")


class DatabaseTransaction:
    """Class-based custom context manager implementing __enter__ and __exit__.

    Ensures atomic transactions:
    - Commits database modifications when the enclosed block completes successfully.
    - Automatically rolls back any modifications if an unhandled exception occurs.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self._in_transaction = False

    def __enter__(self) -> "DatabaseTransaction":
        # Note: In sqlite3, executing a DML statement opens a transaction.
        # We can explicitly record transaction boundary.
        self._in_transaction = True
        logger.debug("TX_BEGIN | Database transaction started.")
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> bool:
        if exc_type is not None:
            logger.error(
                "TX_ROLLBACK | Transaction rolled back due to error: %s (%s)",
                exc_type.__name__,
                exc_val,
            )
            self.connection.rollback()
            self._in_transaction = False
            # Propagate exception to caller
            return False

        logger.debug("TX_COMMIT | Committing database transaction.")
        self.connection.commit()
        self._in_transaction = False
        return True


@contextmanager
def managed_cursor(
    connection: sqlite3.Connection,
) -> Generator[sqlite3.Cursor, None, None]:
    """Generator-based context manager using @contextmanager.

    Ensures cursor cleanup and resource releasing upon exiting block.
    """
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
