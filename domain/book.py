"""Domain Entity: Book.

Encapsulates state and business invariants for books in the library.
Demonstrates OOP encapsulation and data integrity rules.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from library.exceptions import BookError, BookNotAvailableError


@dataclass
class Book:
    """Represents a book in the library catalog.

    Invariants:
        - 0 <= available_copies <= total_copies
        - total_copies >= 1
    """

    isbn: str
    title: str
    author: str
    genre: str
    total_copies: int
    available_copies: int

    def __post_init__(self) -> None:
        """Validate invariant constraints upon instantiation."""
        if self.total_copies < 1:
            raise BookError("Total copies must be at least 1.")
        if self.available_copies < 0:
            raise BookError("Available copies cannot be negative.")
        if self.available_copies > self.total_copies:
            raise BookError("Available copies cannot exceed total copies.")

    def is_available(self) -> bool:
        """Check whether at least one copy is currently available for borrowing."""
        return self.available_copies > 0

    def borrow_copy(self) -> None:
        """Decrement available copies when a loan is issued.

        Raises:
            BookNotAvailableError: If no copies are currently available.
        """
        if not self.is_available():
            raise BookNotAvailableError(self.isbn, self.title)
        self.available_copies -= 1

    def return_copy(self) -> None:
        """Increment available copies when a loaned book is returned.

        Raises:
            BookError: If returning exceeds total copies held by the library.
        """
        if self.available_copies >= self.total_copies:
            raise BookError(
                f"Cannot return book '{self.title}' (ISBN: {self.isbn}): "
                f"all {self.total_copies} copies are already in library."
            )
        self.available_copies += 1

    def to_dict(self) -> dict:
        """Serialize book state to dictionary."""
        return asdict(self)
