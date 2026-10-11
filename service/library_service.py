"""Application Service Layer: LibraryService.

The central orchestration point for library business workflows.
Adheres strictly to SOLID principles:
- SRP: Coordinates workflows without HTTP or CLI coupling.
- DIP: Depends entirely on abstract repository interfaces.
- DRY: Single source of truth for borrowing, returning, fine calculation, and validation.
- Advanced features: Incorporates generators, decorators, and context managers.
"""

from __future__ import annotations

import logging
import uuid
from datetime import date, timedelta
from typing import Any, Dict, Generator, List, Optional

from library.config import LibraryConfig
from library.context_managers import DatabaseTransaction
from library.decorators import audit_log
from library.domain.book import Book
from library.domain.loan import Loan
from library.domain.member import Member, create_member
from library.exceptions import (
    BookAlreadyBorrowedError,
    BookNotFoundError,
    BorrowLimitExceededError,
    LoanNotFoundError,
    MemberNotFoundError,
)
from library.infrastructure.database import DatabaseManager
from library.infrastructure.sqlite_repos import (
    SQLiteBookRepository,
    SQLiteLoanRepository,
    SQLiteMemberRepository,
)
from library.interfaces.repositories import (
    BookRepository,
    LoanRepository,
    MemberRepository,
)
from library.validators import (
    validate_email,
    validate_genre,
    validate_isbn,
    validate_member_id,
    validate_non_empty_string,
    validate_positive_integer,
)

logger = logging.getLogger("library.service")


class LibraryService:
    """Core library service implementing business logic and transactions."""

    def __init__(
        self,
        book_repo: BookRepository,
        member_repo: MemberRepository,
        loan_repo: LoanRepository,
        config: LibraryConfig,
        db_manager: Optional[DatabaseManager] = None,
    ) -> None:
        self._book_repo = book_repo
        self._member_repo = member_repo
        self._loan_repo = loan_repo
        self._config = config
        self._db_manager = db_manager

    @property
    def config(self) -> LibraryConfig:
        """Read-only access to current library configuration."""
        return self._config

    @classmethod
    def create_default(cls, config: Optional[LibraryConfig] = None) -> "LibraryService":
        """Factory method to construct LibraryService with SQLite infrastructure.

        Args:
            config: Optional configuration instance. Defaults to loading from environment.

        Returns:
            Fully assembled LibraryService instance.
        """
        cfg = config or LibraryConfig.load()
        db_mgr = DatabaseManager(cfg.db_path)
        conn = db_mgr.get_connection()
        return cls(
            book_repo=SQLiteBookRepository(conn),
            member_repo=SQLiteMemberRepository(conn),
            loan_repo=SQLiteLoanRepository(conn),
            config=cfg,
            db_manager=db_mgr,
        )

    # =========================================================================
    # Book Operations
    # =========================================================================

    def add_book(
        self,
        title: str,
        author: str,
        isbn: str,
        genre: str,
        total_copies: int = 1,
    ) -> Book:
        """Add a new book title to the catalog with validation.

        Args:
            title: Title of the book.
            author: Author of the book.
            isbn: Raw ISBN string.
            genre: Genre name (must match joiner's personalized allowed genres).
            total_copies: Initial inventory count (>= 1).

        Returns:
            Created Book entity.
        """
        clean_isbn = validate_isbn(isbn)
        clean_title = validate_non_empty_string("title", title)
        clean_author = validate_non_empty_string("author", author)
        clean_genre = validate_genre(genre, self._config.genres)
        clean_copies = validate_positive_integer("total_copies", total_copies)

        book = Book(
            isbn=clean_isbn,
            title=clean_title,
            author=clean_author,
            genre=clean_genre,
            total_copies=clean_copies,
            available_copies=clean_copies,
        )

        if self._db_manager:
            with self._db_manager.transaction():
                self._book_repo.add(book)
        else:
            self._book_repo.add(book)

        logger.info("BOOK_ADDED | ISBN: %s | Title: %s", clean_isbn, clean_title)
        return book

    def get_book(self, isbn: str) -> Book:
        """Retrieve a book by ISBN.

        Raises:
            BookNotFoundError: If no matching book is cataloged.
        """
        clean_isbn = validate_isbn(isbn)
        book = self._book_repo.get_by_isbn(clean_isbn)
        if not book:
            raise BookNotFoundError(clean_isbn)
        return book

    def search_books(
        self, query: Optional[str] = None, genre: Optional[str] = None
    ) -> List[Book]:
        """Search books by partial title/author query and/or genre."""
        return self._book_repo.search(query=query, genre=genre)

    # =========================================================================
    # Member Operations
    # =========================================================================

    def register_member(
        self,
        member_id: str,
        name: str,
        email: str,
        member_type: str = "student",
    ) -> Member:
        """Register a new member in the library.

        Args:
            member_id: Alphanumeric member identifier.
            name: Full name.
            email: Valid email address.
            member_type: 'student', 'staff', or 'faculty'.

        Returns:
            Instantiated concrete Member subclass.
        """
        clean_id = validate_member_id(member_id)
        clean_name = validate_non_empty_string("name", name)
        clean_email = validate_email(email)

        m_type = member_type.lower().strip()
        if m_type == "student":
            borrow_limit = self._config.student_borrow_limit
        elif m_type == "staff":
            borrow_limit = self._config.staff_borrow_limit
        elif m_type == "faculty":
            borrow_limit = 10
        else:
            raise ValueError(f"Unknown member type '{member_type}'.")

        member = create_member(
            member_type=m_type,
            member_id=clean_id,
            name=clean_name,
            email=clean_email,
            borrow_limit=borrow_limit,
        )

        if self._db_manager:
            with self._db_manager.transaction():
                self._member_repo.add(member)
        else:
            self._member_repo.add(member)

        logger.info("MEMBER_REGISTERED | ID: %s | Type: %s", clean_id, m_type)
        return member

    def get_member(self, member_id: str) -> Member:
        """Retrieve a member by ID.

        Raises:
            MemberNotFoundError: If the member does not exist.
        """
        clean_id = validate_member_id(member_id)
        member = self._member_repo.get_by_id(clean_id)
        if not member:
            raise MemberNotFoundError(clean_id)
        return member

    def get_member_status(self, member_id: str) -> Dict[str, Any]:
        """Retrieve member information along with current loans and overdue fines."""
        member = self.get_member(member_id)
        active_loans = self._loan_repo.get_active_loans_by_member(member.member_id)
        all_loans = self._loan_repo.get_all_loans_by_member(member.member_id)

        today = date.today()
        active_loan_details = []
        total_overdue_fines = 0.0

        for loan in active_loans:
            fine = loan.calculate_fine(self._config.fine_per_day, as_of=today)
            total_overdue_fines += fine
            active_loan_details.append({
                **loan.to_dict(),
                "days_overdue": loan.calculate_overdue_days(as_of=today),
                "current_fine": fine,
            })

        return {
            "member": member.to_dict(),
            "active_loans_count": len(active_loans),
            "borrow_limit": member.borrow_limit,
            "remaining_borrow_capacity": max(0, member.borrow_limit - len(active_loans)),
            "active_loans": active_loan_details,
            "total_loans_history_count": len(all_loans),
            "total_pending_fines": round(total_overdue_fines, 2),
        }

    # =========================================================================
    # Loan Operations (Borrow & Return with Decorators & Transactions)
    # =========================================================================

    @audit_log("borrow_book")
    def borrow_book(
        self,
        member_id: str,
        isbn: str,
        borrow_date: Optional[date] = None,
    ) -> Loan:
        """Issue a book loan to an authorized member.

        Atomic operation wrapped with custom transaction context manager.
        Decorated with @audit_log to record actions.

        Raises:
            MemberNotFoundError: If member does not exist.
            BookNotFoundError: If book does not exist.
            BookAlreadyBorrowedError: If member already holds a copy.
            BorrowLimitExceededError: If member has reached borrowing quota.
            BookNotAvailableError: If inventory is exhausted.
        """
        clean_id = validate_member_id(member_id)
        clean_isbn = validate_isbn(isbn)
        effective_date = borrow_date or date.today()

        member = self.get_member(clean_id)
        book = self.get_book(clean_isbn)

        # Invariant: A member cannot borrow two copies of the same book simultaneously
        existing_loan = self._loan_repo.get_active_loan(clean_isbn, clean_id)
        if existing_loan:
            raise BookAlreadyBorrowedError(clean_id, clean_isbn)

        # Invariant: Member borrow quota check (polymorphism via can_borrow)
        active_loans = self._loan_repo.get_active_loans_by_member(clean_id)
        if not member.can_borrow(len(active_loans)):
            raise BorrowLimitExceededError(
                member_id=clean_id,
                limit=member.borrow_limit,
                current_count=len(active_loans),
            )

        # Invariant: Available copies check
        book.borrow_copy()

        # Due date calculation based on polymorphic member loan duration
        due_date = effective_date + timedelta(days=member.default_loan_days)
        loan_id = f"LOAN-{uuid.uuid4().hex[:8].upper()}"

        loan = Loan(
            loan_id=loan_id,
            isbn=clean_isbn,
            member_id=clean_id,
            borrow_date=effective_date,
            due_date=due_date,
        )

        def _persist() -> None:
            self._book_repo.update(book)
            self._loan_repo.add(loan)

        if self._db_manager:
            with self._db_manager.transaction():
                _persist()
        else:
            _persist()

        logger.info(
            "LOAN_CREATED | Loan: %s | Member: %s | ISBN: %s | Due: %s",
            loan_id,
            clean_id,
            clean_isbn,
            due_date.isoformat(),
        )
        return loan

    @audit_log("return_book")
    def return_book(
        self,
        member_id: str,
        isbn: str,
        return_date: Optional[date] = None,
        fine_paid: bool = False,
    ) -> Dict[str, Any]:
        """Process the return of a borrowed book and compute applicable overdue fines.

        Atomic operation wrapped with custom transaction context manager.
        Decorated with @audit_log to record actions.

        Raises:
            MemberNotFoundError: If member does not exist.
            BookNotFoundError: If book does not exist.
            LoanNotFoundError: If no active loan exists for this book/member.
        """
        clean_id = validate_member_id(member_id)
        clean_isbn = validate_isbn(isbn)
        effective_return_date = return_date or date.today()

        # Validate existence
        self.get_member(clean_id)
        book = self.get_book(clean_isbn)

        loan = self._loan_repo.get_active_loan(clean_isbn, clean_id)
        if not loan:
            raise LoanNotFoundError(
                details=f"No active loan found for member '{clean_id}' and book '{clean_isbn}'."
            )

        # Close loan and calculate fine using assigned fine_per_day
        fine = loan.close_loan(
            return_date=effective_return_date,
            fine_per_day=self._config.fine_per_day,
        )
        loan.fine_paid = fine_paid
        book.return_copy()

        def _persist() -> None:
            self._loan_repo.update(loan)
            self._book_repo.update(book)

        if self._db_manager:
            with self._db_manager.transaction():
                _persist()
        else:
            _persist()

        logger.info(
            "LOAN_RETURNED | Loan: %s | Member: %s | ISBN: %s | Overdue Fine: $%.2f",
            loan.loan_id,
            clean_id,
            clean_isbn,
            fine,
        )

        return {
            "loan": loan.to_dict(),
            "fine_amount": fine,
            "days_overdue": loan.calculate_overdue_days(effective_return_date),
            "book_title": book.title,
            "fine_per_day": self._config.fine_per_day,
        }

    # =========================================================================
    # Generator Functions (Section 3.2 Requirement)
    # =========================================================================

    def iter_catalog(
        self, genre: Optional[str] = None
    ) -> Generator[Book, None, None]:
        """Lazy generator yielding catalog books one by one.

        Prevents constructing the complete list in memory simultaneously.
        Satisfies generator function requirement in Section 3.2.
        """
        books = self._book_repo.search(genre=genre)
        for book in books:
            yield book

    def iter_overdue_loans(
        self, as_of_date: Optional[date] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Lazy generator yielding active overdue loans one by one with calculated fines.

        Prevents loading large overdue lists entirely into memory.
        Satisfies generator function requirement in Section 3.2.
        """
        ref_date = as_of_date or date.today()
        active_loans = self._loan_repo.list_active_loans()

        for loan in active_loans:
            if loan.is_overdue(as_of=ref_date):
                member = self._member_repo.get_by_id(loan.member_id)
                book = self._book_repo.get_by_isbn(loan.isbn)
                overdue_days = loan.calculate_overdue_days(as_of=ref_date)
                fine = loan.calculate_fine(self._config.fine_per_day, as_of=ref_date)

                yield {
                    "loan_id": loan.loan_id,
                    "isbn": loan.isbn,
                    "book_title": book.title if book else "Unknown",
                    "member_id": loan.member_id,
                    "member_name": member.name if member else "Unknown",
                    "borrow_date": loan.borrow_date.isoformat(),
                    "due_date": loan.due_date.isoformat(),
                    "days_overdue": overdue_days,
                    "fine_amount": fine,
                }
