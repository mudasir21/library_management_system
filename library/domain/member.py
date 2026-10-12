"""Domain Entities: Member hierarchy with Abstract Base Class.

Demonstrates OOP:
- Abstraction: abc.ABC enforcing `can_borrow()` and contract methods
- Inheritance: Student and Staff inheriting from Member base class
- Polymorphism: Borrowing rules, limits, and loan periods vary across member types
- SOLID:
    - OCP: Adding Faculty requires creating a new subclass without modifying existing ones
    - LSP: Subclasses can substitute Member without altering borrowing validation logic
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class Member(ABC):
    """Abstract Base Class defining the contract for all library patrons."""

    def __init__(self, member_id: str, name: str, email: str, borrow_limit: int) -> None:
        if not member_id or not name or not email:
            raise ValueError("member_id, name, and email must be non-empty strings.")
        if borrow_limit < 1:
            raise ValueError("borrow_limit must be at least 1.")

        self._member_id = member_id
        self._name = name
        self._email = email
        self._borrow_limit = borrow_limit

    @property
    def member_id(self) -> str:
        """Unique identifier of the member."""
        return self._member_id

    @property
    def name(self) -> str:
        """Full name of the member."""
        return self._name

    @property
    def email(self) -> str:
        """Contact email address of the member."""
        return self._email

    @property
    def borrow_limit(self) -> int:
        """Maximum number of active book loans permitted for this member."""
        return self._borrow_limit

    @property
    @abstractmethod
    def member_type(self) -> str:
        """Discriminator string identifying the concrete member type."""
        pass

    @property
    @abstractmethod
    def default_loan_days(self) -> int:
        """Default borrowing duration in days for this member type."""
        pass

    @abstractmethod
    def can_borrow(self, current_active_loans_count: int) -> bool:
        """Determine whether the member is eligible to borrow another book.

        Args:
            current_active_loans_count: The number of active loans currently held.

        Returns:
            True if member has borrowing capacity, False otherwise.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize member state to dictionary."""
        return {
            "member_id": self.member_id,
            "name": self.name,
            "email": self.email,
            "member_type": self.member_type,
            "borrow_limit": self.borrow_limit,
            "default_loan_days": self.default_loan_days,
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.member_id!r}, name={self.name!r}, "
            f"limit={self.borrow_limit})"
        )


class Student(Member):
    """Student member type with personalized borrowing rules."""

    DEFAULT_LOAN_DAYS = 14

    def __init__(self, member_id: str, name: str, email: str, borrow_limit: int = 4) -> None:
        super().__init__(member_id=member_id, name=name, email=email, borrow_limit=borrow_limit)

    @property
    def member_type(self) -> str:
        return "student"

    @property
    def default_loan_days(self) -> int:
        return self.DEFAULT_LOAN_DAYS

    def can_borrow(self, current_active_loans_count: int) -> bool:
        """Students can borrow if they hold fewer loans than their student_borrow_limit."""
        return current_active_loans_count < self.borrow_limit


class Staff(Member):
    """Staff member type with personalized borrowing rules."""

    DEFAULT_LOAN_DAYS = 28

    def __init__(self, member_id: str, name: str, email: str, borrow_limit: int = 6) -> None:
        super().__init__(member_id=member_id, name=name, email=email, borrow_limit=borrow_limit)

    @property
    def member_type(self) -> str:
        return "staff"

    @property
    def default_loan_days(self) -> int:
        return self.DEFAULT_LOAN_DAYS

    def can_borrow(self, current_active_loans_count: int) -> bool:
        """Staff members can borrow if they hold fewer loans than their staff_borrow_limit."""
        return current_active_loans_count < self.borrow_limit


class Faculty(Member):
    """Faculty member type demonstrating Open/Closed Principle (OCP) extension."""

    DEFAULT_LOAN_DAYS = 60

    def __init__(self, member_id: str, name: str, email: str, borrow_limit: int = 10) -> None:
        super().__init__(member_id=member_id, name=name, email=email, borrow_limit=borrow_limit)

    @property
    def member_type(self) -> str:
        return "faculty"

    @property
    def default_loan_days(self) -> int:
        return self.DEFAULT_LOAN_DAYS

    def can_borrow(self, current_active_loans_count: int) -> bool:
        """Faculty members have extended privileges."""
        return current_active_loans_count < self.borrow_limit


def create_member(
    member_type: str,
    member_id: str,
    name: str,
    email: str,
    borrow_limit: int | None = None,
) -> Member:
    """Factory function to instantiate concrete Member subclasses based on type string.

    Args:
        member_type: 'student', 'staff', or 'faculty'
        member_id: Unique member identifier
        name: Full name
        email: Email address
        borrow_limit: Optional custom borrow limit, falls back to default

    Returns:
        Concrete Member instance.

    Raises:
        ValueError: If member_type is unrecognized.
    """
    m_type = member_type.lower().strip()
    if m_type == "student":
        return Student(
            member_id=member_id,
            name=name,
            email=email,
            borrow_limit=borrow_limit if borrow_limit is not None else 4,
        )
    if m_type == "staff":
        return Staff(
            member_id=member_id,
            name=name,
            email=email,
            borrow_limit=borrow_limit if borrow_limit is not None else 6,
        )
    if m_type == "faculty":
        return Faculty(
            member_id=member_id,
            name=name,
            email=email,
            borrow_limit=borrow_limit if borrow_limit is not None else 10,
        )
    raise ValueError(f"Unknown member type '{member_type}'. Permitted: student, staff, faculty.")
