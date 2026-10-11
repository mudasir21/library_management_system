"""SQLite Concrete Repository Implementations.

Implements abstract repository interfaces defined in `library.interfaces.repositories`.
Satisfies Dependency Inversion Principle (DIP) and single responsibility for storage.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import List, Optional

from library.domain.book import Book
from library.domain.loan import Loan
from library.domain.member import Member, create_member
from library.exceptions import (
    DuplicateBookError,
    DuplicateMemberError,
    PersistenceError,
)
from library.interfaces.repositories import (
    BookRepository,
    LoanRepository,
    MemberRepository,
)


class SQLiteBookRepository(BookRepository):
    """SQLite implementation of BookRepository."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, book: Book) -> None:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO books (isbn, title, author, genre, total_copies, available_copies)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    book.isbn,
                    book.title,
                    book.author,
                    book.genre,
                    book.total_copies,
                    book.available_copies,
                ),
            )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" in str(exc) or "PRIMARY KEY" in str(exc):
                raise DuplicateBookError(book.isbn)
            raise PersistenceError(f"Failed to persist book: {exc}")

    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT isbn, title, author, genre, total_copies, available_copies
            FROM books WHERE isbn = ?
            """,
            (isbn,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Book(
            isbn=row["isbn"],
            title=row["title"],
            author=row["author"],
            genre=row["genre"],
            total_copies=row["total_copies"],
            available_copies=row["available_copies"],
        )

    def update(self, book: Book) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE books
            SET title = ?, author = ?, genre = ?, total_copies = ?, available_copies = ?
            WHERE isbn = ?
            """,
            (
                book.title,
                book.author,
                book.genre,
                book.total_copies,
                book.available_copies,
                book.isbn,
            ),
        )

    def list_all(self) -> List[Book]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT isbn, title, author, genre, total_copies, available_copies
            FROM books ORDER BY title ASC
            """
        )
        return [
            Book(
                isbn=row["isbn"],
                title=row["title"],
                author=row["author"],
                genre=row["genre"],
                total_copies=row["total_copies"],
                available_copies=row["available_copies"],
            )
            for row in cursor.fetchall()
        ]

    def search(
        self, query: Optional[str] = None, genre: Optional[str] = None
    ) -> List[Book]:
        cursor = self.connection.cursor()
        clauses = []
        params = []

        if query:
            wildcard = f"%{query.strip()}%"
            clauses.append("(title LIKE ? OR author LIKE ?)")
            params.extend([wildcard, wildcard])

        if genre:
            clauses.append("LOWER(genre) = LOWER(?)")
            params.append(genre.strip())

        sql = "SELECT isbn, title, author, genre, total_copies, available_copies FROM books"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY title ASC"

        cursor.execute(sql, params)
        return [
            Book(
                isbn=row["isbn"],
                title=row["title"],
                author=row["author"],
                genre=row["genre"],
                total_copies=row["total_copies"],
                available_copies=row["available_copies"],
            )
            for row in cursor.fetchall()
        ]


class SQLiteMemberRepository(MemberRepository):
    """SQLite implementation of MemberRepository."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def add(self, member: Member) -> None:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO members (member_id, name, email, member_type, borrow_limit)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    member.member_id,
                    member.name,
                    member.email,
                    member.member_type,
                    member.borrow_limit,
                ),
            )
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed" in str(exc) or "PRIMARY KEY" in str(exc):
                raise DuplicateMemberError(member.member_id)
            raise PersistenceError(f"Failed to persist member: {exc}")

    def get_by_id(self, member_id: str) -> Optional[Member]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT member_id, name, email, member_type, borrow_limit
            FROM members WHERE member_id = ?
            """,
            (member_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return create_member(
            member_type=row["member_type"],
            member_id=row["member_id"],
            name=row["name"],
            email=row["email"],
            borrow_limit=row["borrow_limit"],
        )

    def list_all(self) -> List[Member]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT member_id, name, email, member_type, borrow_limit
            FROM members ORDER BY name ASC
            """
        )
        return [
            create_member(
                member_type=row["member_type"],
                member_id=row["member_id"],
                name=row["name"],
                email=row["email"],
                borrow_limit=row["borrow_limit"],
            )
            for row in cursor.fetchall()
        ]


class SQLiteLoanRepository(LoanRepository):
    """SQLite implementation of LoanRepository."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    @staticmethod
    def _row_to_loan(row: sqlite3.Row) -> Loan:
        return Loan(
            loan_id=row["loan_id"],
            isbn=row["isbn"],
            member_id=row["member_id"],
            borrow_date=date.fromisoformat(row["borrow_date"]),
            due_date=date.fromisoformat(row["due_date"]),
            return_date=date.fromisoformat(row["return_date"]) if row["return_date"] else None,
            fine_amount=float(row["fine_amount"]),
            fine_paid=bool(row["fine_paid"]),
        )

    def add(self, loan: Loan) -> None:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO loans (loan_id, isbn, member_id, borrow_date, due_date, return_date, fine_amount, fine_paid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    loan.loan_id,
                    loan.isbn,
                    loan.member_id,
                    loan.borrow_date.isoformat(),
                    loan.due_date.isoformat(),
                    loan.return_date.isoformat() if loan.return_date else None,
                    loan.fine_amount,
                    1 if loan.fine_paid else 0,
                ),
            )
        except sqlite3.Error as exc:
            raise PersistenceError(f"Failed to record loan: {exc}")

    def get_by_id(self, loan_id: str) -> Optional[Loan]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT loan_id, isbn, member_id, borrow_date, due_date, return_date, fine_amount, fine_paid
            FROM loans WHERE loan_id = ?
            """,
            (loan_id,),
        )
        row = cursor.fetchone()
        return self._row_to_loan(row) if row else None

    def get_active_loan(self, isbn: str, member_id: str) -> Optional[Loan]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT loan_id, isbn, member_id, borrow_date, due_date, return_date, fine_amount, fine_paid
            FROM loans
            WHERE isbn = ? AND member_id = ? AND return_date IS NULL
            ORDER BY borrow_date DESC LIMIT 1
            """,
            (isbn, member_id),
        )
        row = cursor.fetchone()
        return self._row_to_loan(row) if row else None

    def get_active_loans_by_member(self, member_id: str) -> List[Loan]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT loan_id, isbn, member_id, borrow_date, due_date, return_date, fine_amount, fine_paid
            FROM loans
            WHERE member_id = ? AND return_date IS NULL
            ORDER BY due_date ASC
            """,
            (member_id,),
        )
        return [self._row_to_loan(row) for row in cursor.fetchall()]

    def get_all_loans_by_member(self, member_id: str) -> List[Loan]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT loan_id, isbn, member_id, borrow_date, due_date, return_date, fine_amount, fine_paid
            FROM loans
            WHERE member_id = ?
            ORDER BY borrow_date DESC
            """,
            (member_id,),
        )
        return [self._row_to_loan(row) for row in cursor.fetchall()]

    def update(self, loan: Loan) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE loans
            SET return_date = ?, fine_amount = ?, fine_paid = ?
            WHERE loan_id = ?
            """,
            (
                loan.return_date.isoformat() if loan.return_date else None,
                loan.fine_amount,
                1 if loan.fine_paid else 0,
                loan.loan_id,
            ),
        )

    def list_active_loans(self) -> List[Loan]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT loan_id, isbn, member_id, borrow_date, due_date, return_date, fine_amount, fine_paid
            FROM loans
            WHERE return_date IS NULL
            ORDER BY due_date ASC
            """
        )
        return [self._row_to_loan(row) for row in cursor.fetchall()]

    def list_all(self) -> List[Loan]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT loan_id, isbn, member_id, borrow_date, due_date, return_date, fine_amount, fine_paid
            FROM loans
            ORDER BY borrow_date DESC
            """
        )
        return [self._row_to_loan(row) for row in cursor.fetchall()]
