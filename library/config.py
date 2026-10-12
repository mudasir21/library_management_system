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



