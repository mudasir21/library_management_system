"""Domain Entity: Loan.

Encapsulates loan lifecycle, due dates, and fine calculations using the assigned
fine_per_day parameter. Demonstrates high cohesion and single responsibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional


@dataclass
class Loan:
    """Represents a book borrowing transaction."""

    loan_id: str
    isbn: str
    member_id: str
    borrow_date: date
    due_date: date
    return_date: Optional[date] = None
    fine_amount: float = 0.0
    fine_paid: bool = False

    @property
    def is_active(self) -> bool:
        """True if the book has not yet been returned."""
        return self.return_date is None

    def is_overdue(self, as_of: Optional[date] = None) -> bool:
        """Check whether the loan is past its due date without having been returned."""
        if not self.is_active:
            return False
        reference_date = as_of or date.today()
        return reference_date > self.due_date

    def calculate_overdue_days(self, as_of: Optional[date] = None) -> int:
        """Calculate the number of days overdue.

        For returned loans, computes days past due when returned.
        For active loans, computes days past due as of the given date.
        """
        target_date = self.return_date or (as_of or date.today())
        if target_date > self.due_date:
            return (target_date - self.due_date).days
        return 0

    def calculate_fine(self, fine_per_day: float, as_of: Optional[date] = None) -> float:
        """Calculate the monetary fine for this loan using the assigned daily fine rate.

        Args:
            fine_per_day: Daily fine rate assigned to the joiner.
            as_of: Reference date for active loans (defaults to today).

        Returns:
            Calculated fine rounded to 2 decimal places.
        """
        days_overdue = self.calculate_overdue_days(as_of)
        return round(days_overdue * fine_per_day, 2)

    def close_loan(self, return_date: date, fine_per_day: float) -> float:
        """Mark the loan as returned and compute the final fine.

        Args:
            return_date: Date on which the book was returned.
            fine_per_day: Assigned daily rate for overdue fines.

        Returns:
            Final fine amount.
        """
        self.return_date = return_date
        self.fine_amount = self.calculate_fine(fine_per_day, as_of=return_date)
        return self.fine_amount

    def to_dict(self) -> Dict[str, Any]:
        """Serialize loan record to dictionary."""
        return {
            "loan_id": self.loan_id,
            "isbn": self.isbn,
            "member_id": self.member_id,
            "borrow_date": self.borrow_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "fine_amount": self.fine_amount,
            "fine_paid": self.fine_paid,
            "is_active": self.is_active,
        }
