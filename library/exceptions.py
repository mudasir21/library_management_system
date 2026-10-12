"""Custom Exception Hierarchy for Library Management System.

Explicitly defined custom domain exceptions conforming to requirements in
Section 3.2. Avoids reliance on generic Python exceptions to ensure structured,
predictable, and type-safe error handling across domain, service, CLI, and API layers.
"""

from __future__ import annotations


class LibraryError(Exception):
    """Base class for all library domain exceptions."""

    def __init__(self, message: str, code: str = "LIBRARY_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


# =====================================================================
# Book-related Exceptions
# =====================================================================

class BookError(LibraryError):
    """Base exception for book-related domain errors."""

    def __init__(self, message: str, code: str = "BOOK_ERROR") -> None:
        super().__init__(message, code=code)


class BookNotFoundError(BookError):
    """Raised when a book with the given identifier/ISBN cannot be found."""

    def __init__(self, isbn: str) -> None:
        super().__init__(f"Book with ISBN '{isbn}' was not found.", code="BOOK_NOT_FOUND")
        self.isbn = isbn


class BookNotAvailableError(BookError):
    """Raised when all copies of a book are currently borrowed."""

    def __init__(self, isbn: str, title: str | None = None) -> None:
        detail = f" '{title}'" if title else ""
        super().__init__(
            f"Book{detail} (ISBN: {isbn}) has no available copies to borrow.",
            code="BOOK_NOT_AVAILABLE",
        )
        self.isbn = isbn


class DuplicateBookError(BookError):
    """Raised when attempting to add a book that already exists."""

    def __init__(self, isbn: str) -> None:
        super().__init__(f"Book with ISBN '{isbn}' already exists in catalog.", code="DUPLICATE_BOOK")
        self.isbn = isbn


# =====================================================================
# Member-related Exceptions
# =====================================================================

class MemberError(LibraryError):
    """Base exception for member-related domain errors."""

    def __init__(self, message: str, code: str = "MEMBER_ERROR") -> None:
        super().__init__(message, code=code)


class MemberNotFoundError(MemberError):
    """Raised when a member with the given ID cannot be found."""

    def __init__(self, member_id: str) -> None:
        super().__init__(f"Member with ID '{member_id}' was not found.", code="MEMBER_NOT_FOUND")
        self.member_id = member_id


class BorrowLimitExceededError(MemberError):
    """Raised when a member attempts to borrow beyond their allowed quota."""

    def __init__(self, member_id: str, limit: int, current_count: int) -> None:
        super().__init__(
            f"Member '{member_id}' has reached borrowing limit of {limit} "
            f"(currently holding {current_count} active loans).",
            code="BORROW_LIMIT_EXCEEDED",
        )
        self.member_id = member_id
        self.limit = limit
        self.current_count = current_count


class DuplicateMemberError(MemberError):
    """Raised when attempting to register a member with an existing ID."""

    def __init__(self, member_id: str) -> None:
        super().__init__(f"Member with ID '{member_id}' is already registered.", code="DUPLICATE_MEMBER")
        self.member_id = member_id


# =====================================================================
# Loan-related Exceptions
# =====================================================================

class LoanError(LibraryError):
    """Base exception for loan-related domain errors."""

    def __init__(self, message: str, code: str = "LOAN_ERROR") -> None:
        super().__init__(message, code=code)


class LoanNotFoundError(LoanError):
    """Raised when a loan record cannot be found."""

    def __init__(self, loan_id: str | None = None, details: str | None = None) -> None:
        msg = f"Loan '{loan_id}' not found." if loan_id else (details or "Active loan not found.")
        super().__init__(msg, code="LOAN_NOT_FOUND")
        self.loan_id = loan_id


class BookAlreadyBorrowedError(LoanError):
    """Raised when a member attempts to borrow a copy of a book they already currently hold."""

    def __init__(self, member_id: str, isbn: str) -> None:
        super().__init__(
            f"Member '{member_id}' already has an active loan for book '{isbn}'.",
            code="BOOK_ALREADY_BORROWED",
        )
        self.member_id = member_id
        self.isbn = isbn


class LoanAlreadyReturnedError(LoanError):
    """Raised when attempting to return a loan that has already been returned."""

    def __init__(self, loan_id: str) -> None:
        super().__init__(f"Loan '{loan_id}' has already been marked as returned.", code="LOAN_ALREADY_RETURNED")
        self.loan_id = loan_id


# =====================================================================
# Validation Exceptions
# =====================================================================

class ValidationError(LibraryError):
    """Base exception for input validation failures."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message, code=code)


class InvalidISBNError(ValidationError):
    """Raised when an ISBN string does not match standard ISBN-10 or ISBN-13 format/checksum."""

    def __init__(self, isbn: str, reason: str = "Invalid ISBN format") -> None:
        super().__init__(f"Invalid ISBN '{isbn}': {reason}.", code="INVALID_ISBN")
        self.isbn = isbn


class InvalidEmailError(ValidationError):
    """Raised when an email address does not match regular expression rules."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Invalid email address '{email}'.", code="INVALID_EMAIL")
        self.email = email


class InvalidGenreError(ValidationError):
    """Raised when a book genre is outside the permitted personalized genres."""

    def __init__(self, genre: str, allowed_genres: list[str]) -> None:
        super().__init__(
            f"Genre '{genre}' is not allowed. Permitted genres: {', '.join(allowed_genres)}.",
            code="INVALID_GENRE",
        )
        self.genre = genre
        self.allowed_genres = allowed_genres


class InvalidInputError(ValidationError):
    """Raised when any required input field is invalid or missing."""

    def __init__(self, field_name: str, reason: str) -> None:
        super().__init__(f"Invalid input for field '{field_name}': {reason}.", code="INVALID_INPUT")
        self.field_name = field_name


# =====================================================================
# Persistence / Infrastructure Exceptions
# =====================================================================

class PersistenceError(LibraryError):
    """Base exception for storage and persistence failures."""

    def __init__(self, message: str, code: str = "PERSISTENCE_ERROR") -> None:
        super().__init__(message, code=code)
