"""Regular Expression and Input Validation Module.

Encapsulates regex-based validation for ISBNs, email addresses, and identifiers
satisfying Section 3.2 and Section 3.4. Reusable across CLI and API layers (DRY).
"""

from __future__ import annotations

import re
from typing import Sequence

from library.exceptions import (
    InvalidEmailError,
    InvalidGenreError,
    InvalidInputError,
    InvalidISBNError,
)

# Regular expression pattern for ISBN-10 (with optional hyphens or spaces)
ISBN10_PATTERN = re.compile(r"^(?:\d[\s-]?){9}[\dXx]$")

# Regular expression pattern for ISBN-13 (with optional hyphens or spaces)
ISBN13_PATTERN = re.compile(r"^(?:97[89][\s-]?)?(?:\d[\s-]?){10}$")

# Regular expression pattern for RFC-compliant email address validation
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*(?:\.[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*)+$"
)

# Regular expression for Member ID: alphanumeric with optional hyphens/underscores
MEMBER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,32}$")


def normalize_isbn(isbn: str) -> str:
    """Strip hyphens and spaces from an ISBN string, converting X to uppercase."""
    return re.sub(r"[\s-]", "", isbn).upper()


def _is_valid_isbn10_checksum(digits: str) -> bool:
    """Validate checksum for a normalized 10-character ISBN."""
    if len(digits) != 10:
        return False
    total = 0
    for idx, char in enumerate(digits):
        val = 10 if char == 'X' else int(char)
        total += val * (10 - idx)
    return total % 11 == 0


def _is_valid_isbn13_checksum(digits: str) -> bool:
    """Validate checksum for a normalized 13-character ISBN."""
    if len(digits) != 13 or not digits.isdigit():
        return False
    total = 0
    for idx, char in enumerate(digits):
        weight = 1 if idx % 2 == 0 else 3
        total += int(char) * weight
    return total % 10 == 0


def validate_isbn(isbn: str) -> str:
    """Validate ISBN format using regular expressions and checksum calculation.

    Args:
        isbn: Raw ISBN string.

    Returns:
        Normalized clean ISBN string.

    Raises:
        InvalidISBNError: If ISBN fails regex match or checksum.
    """
    if not isbn or not isinstance(isbn, str):
        raise InvalidISBNError(str(isbn), "ISBN must be a non-empty string")

    trimmed = isbn.strip()
    clean = normalize_isbn(trimmed)

    if len(clean) == 10:
        if not ISBN10_PATTERN.match(trimmed) or not _is_valid_isbn10_checksum(clean):
            raise InvalidISBNError(isbn, "Invalid ISBN-10 format or checksum")
        return clean

    if len(clean) == 13:
        if not ISBN13_PATTERN.match(trimmed) or not _is_valid_isbn13_checksum(clean):
            raise InvalidISBNError(isbn, "Invalid ISBN-13 format or checksum")
        return clean

    raise InvalidISBNError(isbn, "ISBN must be 10 or 13 digits in length")


def validate_email(email: str) -> str:
    """Validate member email address using regular expression.

    Args:
        email: Raw email string.

    Returns:
        Normalized lowercase email string.

    Raises:
        InvalidEmailError: If format does not match regex.
    """
    if not email or not isinstance(email, str):
        raise InvalidEmailError(str(email))

    trimmed = email.strip()
    if not EMAIL_PATTERN.match(trimmed):
        raise InvalidEmailError(trimmed)

    return trimmed.lower()


def validate_member_id(member_id: str) -> str:
    """Validate member ID format using regular expression."""
    if not member_id or not isinstance(member_id, str):
        raise InvalidInputError("member_id", "Member ID must be a non-empty string")

    trimmed = member_id.strip()
    if not MEMBER_ID_PATTERN.match(trimmed):
        raise InvalidInputError(
            "member_id",
            "Member ID must be 3-32 alphanumeric characters, dashes, or underscores",
        )
    return trimmed


def validate_genre(genre: str, allowed_genres: Sequence[str]) -> str:
    """Validate that book genre is within the permitted personalized genres list."""
    if not genre or not isinstance(genre, str):
        raise InvalidGenreError(str(genre), list(allowed_genres))

    clean = genre.strip()
    # Case-insensitive match against allowed list
    for allowed in allowed_genres:
        if allowed.lower() == clean.lower():
            return allowed

    raise InvalidGenreError(clean, list(allowed_genres))


def validate_positive_integer(field_name: str, value: int, min_val: int = 1) -> int:
    """Validate that integer values like book copies are >= min_val."""
    if not isinstance(value, int) or isinstance(value, bool) or value < min_val:
        raise InvalidInputError(field_name, f"Value must be an integer >= {min_val}")
    return value


def validate_non_empty_string(field_name: str, value: str, max_length: int = 255) -> str:
    """Validate that string fields (e.g. title, author) are non-empty and bounded."""
    if not value or not isinstance(value, str) or not value.strip():
        raise InvalidInputError(field_name, "Value cannot be empty")
    clean = value.strip()
    if len(clean) > max_length:
        raise InvalidInputError(field_name, f"Length exceeds maximum of {max_length} characters")
    return clean
