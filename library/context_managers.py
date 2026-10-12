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


