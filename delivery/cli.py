"""Command-Line Interface (CLI) Module.

Built using Python's `argparse` module satisfying Section 3.2.
Separation of concerns: CLI contains no business logic; it acts as a delivery
adapter delegating all operations to `LibraryService`.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import Optional, Sequence

from library.config import LibraryConfig
from library.exceptions import LibraryError
from library.infrastructure.logging_config import setup_logging
from library.service.library_service import LibraryService


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="library-cli",
        description="Production Library Management System CLI",
    )
    parser.add_argument(
        "--employee-id",
        type=str,
        default=None,
        help="Override joiner employee ID for personalized parameters (default: env or HCL10001)",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to SQLite database file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: add-book
    add_book_parser = subparsers.add_parser("add-book", help="Add a new book to the library")
    add_book_parser.add_argument("--title", required=True, help="Title of the book")
    add_book_parser.add_argument("--author", required=True, help="Author name")
    add_book_parser.add_argument("--isbn", required=True, help="ISBN-10 or ISBN-13 format")
    add_book_parser.add_argument("--genre", required=True, help="Genre of the book")
    add_book_parser.add_argument("--copies", type=int, default=1, help="Total copies to stock (default: 1)")

    # Command: add-member
    add_member_parser = subparsers.add_parser("add-member", help="Register a student, staff, or faculty member")
    add_member_parser.add_argument("--id", required=True, help="Unique member ID (e.g. STU-1001, STF-2001)")
    add_member_parser.add_argument("--name", required=True, help="Full name")
    add_member_parser.add_argument("--email", required=True, help="Valid email address")
    add_member_parser.add_argument(
        "--type",
        choices=["student", "staff", "faculty"],
        default="student",
        help="Member type (default: student)",
    )

    # Command: borrow
    borrow_parser = subparsers.add_parser("borrow", help="Borrow a book for a member")
    borrow_parser.add_argument("--member-id", required=True, help="ID of the borrowing member")
    borrow_parser.add_argument("--isbn", required=True, help="ISBN of the book to borrow")

    # Command: return
    return_parser = subparsers.add_parser("return", help="Return a borrowed book")
    return_parser.add_argument("--member-id", required=True, help="ID of the returning member")
    return_parser.add_argument("--isbn", required=True, help="ISBN of the book being returned")
    return_parser.add_argument("--paid", action="store_true", help="Mark calculated overdue fine as paid")

    # Command: list-books
    list_books_parser = subparsers.add_parser("list-books", help="List and search books in the catalog")
    list_books_parser.add_argument("--genre", help="Filter by specific genre")
    list_books_parser.add_argument("--query", help="Filter by partial title or author match")

    # Command: list-overdue
    list_overdue_parser = subparsers.add_parser("list-overdue", help="List all currently overdue book loans")
    list_overdue_parser.add_argument(
        "--as-of",
        help="Reference date for overdue calculation (YYYY-MM-DD, defaults to today)",
    )

    # Command: member-details
    member_parser = subparsers.add_parser("member-details", help="View member details and active loans")
    member_parser.add_argument("--id", required=True, help="Member ID")

    # Command: config
    subparsers.add_parser("config", help="Display joiner personalized library rules and settings")

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main CLI execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    cfg = LibraryConfig.load(employee_id=args.employee_id, db_path=args.db_path)
    setup_logging(log_file_path=cfg.log_file_path, console_output=False)
    service = LibraryService.create_default(cfg)

    try:
        if args.command == "config":
            print("=" * 60)
            print("Library Personalized Configuration")
            print("=" * 60)
            print(f"Employee ID:          {cfg.employee_id}")
            print(f"Allowed Genres:       {', '.join(cfg.genres)}")
            print(f"Student Borrow Limit: {cfg.student_borrow_limit} books")
            print(f"Staff Borrow Limit:   {cfg.staff_borrow_limit} books")
            print(f"Overdue Fine Rate:    ${cfg.fine_per_day:.2f} / day")
            print(f"Database File:        {cfg.db_path}")
            print("=" * 60)
            return 0

        elif args.command == "add-book":
            book = service.add_book(
                title=args.title,
                author=args.author,
                isbn=args.isbn,
                genre=args.genre,
                total_copies=args.copies,
            )
            print(f"[SUCCESS] Book added successfully:")
            print(f"  Title:     {book.title}")
            print(f"  Author:    {book.author}")
            print(f"  ISBN:      {book.isbn}")
            print(f"  Genre:     {book.genre}")
            print(f"  Copies:    {book.available_copies}/{book.total_copies}")
            return 0

        elif args.command == "add-member":
            member = service.register_member(
                member_id=args.id,
                name=args.name,
                email=args.email,
                member_type=args.type,
            )
            print(f"[SUCCESS] Member registered successfully:")
            print(f"  ID:           {member.member_id}")
            print(f"  Name:         {member.name}")
            print(f"  Email:        {member.email}")
            print(f"  Type:         {member.member_type}")
            print(f"  Borrow Limit: {member.borrow_limit} books")
            return 0

        elif args.command == "borrow":
            loan = service.borrow_book(member_id=args.member_id, isbn=args.isbn)
            print(f"[SUCCESS] Book borrowed successfully:")
            print(f"  Loan ID:     {loan.loan_id}")
            print(f"  Member ID:   {loan.member_id}")
            print(f"  ISBN:        {loan.isbn}")
            print(f"  Borrow Date: {loan.borrow_date}")
            print(f"  Due Date:    {loan.due_date}")
            return 0

        elif args.command == "return":
            res = service.return_book(
                member_id=args.member_id,
                isbn=args.isbn,
                fine_paid=args.paid,
            )
            print(f"[SUCCESS] Book returned successfully:")
            print(f"  Book Title:    {res['book_title']}")
            print(f"  Loan ID:       {res['loan']['loan_id']}")
            print(f"  Days Overdue:  {res['days_overdue']}")
            print(f"  Fine Incurred: ${res['fine_amount']:.2f}")
            if res['fine_amount'] > 0:
                status = "PAID" if args.paid else "UNPAID"
                print(f"  Fine Status:   {status}")
            return 0

        elif args.command == "list-books":
            # Using lazy generator iter_catalog
            found_any = False
            print(f"{'ISBN':<18} {'GENRE':<14} {'AVAILABLE':<10} {'TITLE'}")
            print("-" * 70)
            for book in service.iter_catalog(genre=args.genre):
                if args.query:
                    q = args.query.lower()
                    if q not in book.title.lower() and q not in book.author.lower():
                        continue
                found_any = True
                avail = f"{book.available_copies}/{book.total_copies}"
                print(f"{book.isbn:<18} {book.genre:<14} {avail:<10} {book.title} (by {book.author})")
            if not found_any:
                print("No books found matching the criteria.")
            return 0

        elif args.command == "list-overdue":
            as_of_date = date.fromisoformat(args.as_of) if args.as_of else None
            # Using lazy generator iter_overdue_loans
            found_any = False
            print(f"{'LOAN ID':<16} {'MEMBER':<12} {'DAYS':<6} {'FINE':<10} {'BOOK'}")
            print("-" * 70)
            for item in service.iter_overdue_loans(as_of_date=as_of_date):
                found_any = True
                fine_str = f"${item['fine_amount']:.2f}"
                print(f"{item['loan_id']:<16} {item['member_id']:<12} {item['days_overdue']:<6} {fine_str:<10} {item['book_title']}")
            if not found_any:
                print("No overdue loans found.")
            return 0

        elif args.command == "member-details":
            details = service.get_member_status(args.id)
            mem = details["member"]
            print("=" * 60)
            print(f"Member Details: {mem['name']} ({mem['member_id']})")
            print("=" * 60)
            print(f"Email:             {mem['email']}")
            print(f"Member Type:       {mem['member_type'].capitalize()}")
            print(f"Borrow Quota:      {details['active_loans_count']} / {mem['borrow_limit']} active loans")
            print(f"Total History:     {details['total_loans_history_count']} loans")
            print(f"Pending Fines:     ${details['total_pending_fines']:.2f}")

            if details["active_loans"]:
                print("\nActive Loans:")
                for loan in details["active_loans"]:
                    overdue = f"(OVERDUE: {loan['days_overdue']} days, ${loan['current_fine']:.2f})" if loan['days_overdue'] > 0 else "(On time)"
                    print(f"  - ISBN: {loan['isbn']} | Due: {loan['due_date']} {overdue}")
            print("=" * 60)
            return 0

    except LibraryError as err:
        print(f"[ERROR {err.code}]: {err.message}", file=sys.stderr)
        return 1
    except ValueError as err:
        print(f"[ERROR]: {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
