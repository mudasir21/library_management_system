"""Personalization and Configuration Module.

Implements the deterministic personalization script required by Section 3.1
and provides strongly typed configuration settings for the system.
"""

from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass, field
from typing import List


def get_my_library_parameters(employee_id: str) -> dict:
    """Deterministic, unique library rules per joiner.

    Args:
        employee_id: Unique identifier for the joiner/employee.

    Returns:
        dict containing:
            - genres: 6 deterministic genres chosen from 10 options.
            - student_borrow_limit: integer between 2 and 4.
            - staff_borrow_limit: integer between 5 and 8.
            - fine_per_day: daily fine float between 1.50 and 5.00 rounded to 2 decimals.
    """
    seed = int(hashlib.sha256(('lib-' + employee_id).encode()).hexdigest(), 16) % (2**31)
    rng = random.Random(seed)
    genres = [
        'Fiction', 'Sci-Fi', 'Biography', 'History', 'Technology',
        'Self-Help', 'Mystery', 'Poetry', 'Fantasy', 'Science'
    ]
    return {
        'genres': rng.sample(genres, 6),
        'student_borrow_limit': rng.randint(2, 4),
        'staff_borrow_limit': rng.randint(5, 8),
        'fine_per_day': round(rng.uniform(1.5, 5.0), 2),
    }


@dataclass(frozen=True)
class LibraryConfig:
    """Immutable application configuration with personalized business rules."""

    employee_id: str
    genres: List[str]
    student_borrow_limit: int
    staff_borrow_limit: int
    fine_per_day: float
    db_path: str = "library.db"
    log_file_path: str = "library.log"
    student_loan_days: int = 14
    staff_loan_days: int = 28

    @classmethod
    def load(
        cls,
        employee_id: str | None = None,
        db_path: str | None = None,
        log_file_path: str | None = None,
    ) -> LibraryConfig:
        """Factory method to load configuration from environment or parameters.

        Args:
            employee_id: Optional employee ID. If None, uses LIBRARY_EMPLOYEE_ID or 'HCL10001'.
            db_path: Optional SQLite database file path.
            log_file_path: Optional log file path.

        Returns:
            LibraryConfig instance with deterministic rules populated.
        """
        emp_id = (
            employee_id
            or os.getenv("LIBRARY_EMPLOYEE_ID", "HCL10001")
        ).strip()
        params = get_my_library_parameters(emp_id)

        return cls(
            employee_id=emp_id,
            genres=params['genres'],
            student_borrow_limit=params['student_borrow_limit'],
            staff_borrow_limit=params['staff_borrow_limit'],
            fine_per_day=params['fine_per_day'],
            db_path=db_path or os.getenv("LIBRARY_DB_PATH", "library.db"),
            log_file_path=log_file_path or os.getenv("LIBRARY_LOG_PATH", "library.log"),
            student_loan_days=int(os.getenv("LIBRARY_STUDENT_LOAN_DAYS", "14")),
            staff_loan_days=int(os.getenv("LIBRARY_STAFF_LOAN_DAYS", "28")),
        )
