"""Abstract Repository Interfaces.

Demonstrates SOLID:
- Dependency Inversion Principle (DIP): High-level domain service depends on these
  abstractions rather than concrete SQLite or file persistence.
- Interface Segregation Principle (ISP): Granular, specialized interfaces for books,
  members, and loans, avoiding bloated single-interface antipatterns.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from library.domain.book import Book
from library.domain.loan import Loan
from library.domain.member import Member


class BookRepository(ABC):
    """Abstract interface defining persistence operations for Book entities."""

    @abstractmethod
    def add(self, book: Book) -> None:
        """Add a new book entity to storage."""
        pass

    @abstractmethod
    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        """Retrieve a book by normalized ISBN, or None if not found."""
        pass

    @abstractmethod
    def update(self, book: Book) -> None:
        """Persist modifications to an existing book."""
        pass

    @abstractmethod
    def list_all(self) -> List[Book]:
        """Return all books in storage."""
        pass

    @abstractmethod
    def search(
        self, query: Optional[str] = None, genre: Optional[str] = None
    ) -> List[Book]:
        """Search books matching text title/author query and optional genre."""
        pass


class MemberRepository(ABC):
    """Abstract interface defining persistence operations for Member entities."""

    @abstractmethod
    def add(self, member: Member) -> None:
        """Add a new member entity to storage."""
        pass

    @abstractmethod
    def get_by_id(self, member_id: str) -> Optional[Member]:
        """Retrieve a member by unique member ID, or None if not found."""
        pass

    @abstractmethod
    def list_all(self) -> List[Member]:
        """Return all members in storage."""
        pass


class LoanRepository(ABC):
    """Abstract interface defining persistence operations for Loan entities."""

    @abstractmethod
    def add(self, loan: Loan) -> None:
        """Record a new loan transaction in storage."""
        pass

    @abstractmethod
    def get_by_id(self, loan_id: str) -> Optional[Loan]:
        """Retrieve a loan by unique loan ID, or None if not found."""
        pass

    @abstractmethod
    def get_active_loan(self, isbn: str, member_id: str) -> Optional[Loan]:
        """Retrieve active (unreturned) loan for a specific book and member."""
        pass

    @abstractmethod
    def get_active_loans_by_member(self, member_id: str) -> List[Loan]:
        """Retrieve all currently active loans held by a specific member."""
        pass

    @abstractmethod
    def get_all_loans_by_member(self, member_id: str) -> List[Loan]:
        """Retrieve all loan records (active and returned) for a member."""
        pass

    @abstractmethod
    def update(self, loan: Loan) -> None:
        """Persist state updates to an existing loan (e.g. closure, fines)."""
        pass

    @abstractmethod
    def list_active_loans(self) -> List[Loan]:
        """Return all currently unreturned active loans."""
        pass

    @abstractmethod
    def list_all(self) -> List[Loan]:
        """Return all loans across history."""
        pass
