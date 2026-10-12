"""REST API Layer Module.

Built using FastAPI satisfying Section 3.4 requirements.
Demonstrates layered architecture, separation of concerns, and dependency inversion:
every endpoint delegates to the underlying `LibraryService` without duplicating business logic.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from library.config import LibraryConfig
from library.exceptions import (
    BookAlreadyBorrowedError,
    BookNotAvailableError,
    BookNotFoundError,
    BorrowLimitExceededError,
    DuplicateBookError,
    DuplicateMemberError,
    LibraryError,
    LoanNotFoundError,
    MemberNotFoundError,
    ValidationError,
)
from library.infrastructure.logging_config import setup_logging
from library.service.library_service import LibraryService


# =============================================================================
# Pydantic Request & Response Schemas
# =============================================================================

class AddBookRequest(BaseModel):
    title: str = Field(..., description="Title of the book", min_length=1, max_length=255)
    author: str = Field(..., description="Author of the book", min_length=1, max_length=255)
    isbn: str = Field(..., description="ISBN-10 or ISBN-13 format")
    genre: str = Field(..., description="Genre from permitted personalized genres")
    copies: int = Field(1, description="Number of copies to stock", ge=1)


class AddMemberRequest(BaseModel):
    member_id: str = Field(..., description="Unique alphanumeric member identifier")
    name: str = Field(..., description="Full name of member")
    email: str = Field(..., description="Valid email address")
    member_type: str = Field("student", description="'student', 'staff', or 'faculty'")


class BorrowBookRequest(BaseModel):
    member_id: str = Field(..., description="Member ID")
    isbn: str = Field(..., description="ISBN of book to borrow")
    borrow_date: Optional[date] = Field(None, description="Optional override borrow date (YYYY-MM-DD)")


class ReturnBookRequest(BaseModel):
    member_id: str = Field(..., description="Member ID")
    isbn: str = Field(..., description="ISBN of book to return")
    return_date: Optional[date] = Field(None, description="Optional override return date (YYYY-MM-DD)")
    fine_paid: bool = Field(False, description="Flag indicating if overdue fine was collected")


# =============================================================================
# Application Factory
# =============================================================================

def create_app(service: Optional[LibraryService] = None) -> FastAPI:
    """Factory function creating and configuring the FastAPI application.

    Args:
        service: Optional pre-configured LibraryService instance (useful for tests).
    """
    app = FastAPI(
        title="Library Management System API",
        version="1.0.0",
        description="Production REST API layer delegating to domain LibraryService.",
    )

    # Initialize service if not provided
    app_service = service or LibraryService.create_default()

    # Exception Handlers: translate domain exceptions to HTTP status codes
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(_, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(BookNotFoundError)
    async def book_not_found_handler(_, exc: BookNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(MemberNotFoundError)
    async def member_not_found_handler(_, exc: MemberNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(LoanNotFoundError)
    async def loan_not_found_handler(_, exc: LoanNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(BookNotAvailableError)
    async def book_not_available_handler(_, exc: BookNotAvailableError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(BorrowLimitExceededError)
    async def borrow_limit_handler(_, exc: BorrowLimitExceededError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": exc.code,
                "message": exc.message,
                "limit": exc.limit,
                "current_count": exc.current_count,
            },
        )

    @app.exception_handler(BookAlreadyBorrowedError)
    async def book_already_borrowed_handler(_, exc: BookAlreadyBorrowedError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(DuplicateBookError)
    async def duplicate_book_handler(_, exc: DuplicateBookError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(DuplicateMemberError)
    async def duplicate_member_handler(_, exc: DuplicateMemberError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": exc.code, "message": exc.message},
        )

    @app.exception_handler(LibraryError)
    async def generic_library_error_handler(_, exc: LibraryError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": exc.code, "message": exc.message},
        )

    # Dependency provider
    def get_service() -> LibraryService:
        return app_service

    # =========================================================================
    # Routes
    # =========================================================================

    @app.get("/", response_class=PlainTextResponse, include_in_schema=False)
    def welcome() -> str:
        return (
            "Welcome to HCLTech Library!\n"
            "To explore the library services or test the application, visit:\n"
            "http://127.0.0.1:8000/docs"
        )

    @app.get("/config", summary="Retrieve personalized rules and parameters")
    def get_library_config(svc: LibraryService = Depends(get_service)) -> Dict[str, Any]:
        cfg = svc.config
        return {
            "employee_id": cfg.employee_id,
            "genres": cfg.genres,
            "student_borrow_limit": cfg.student_borrow_limit,
            "staff_borrow_limit": cfg.staff_borrow_limit,
            "fine_per_day": cfg.fine_per_day,
            "student_loan_days": cfg.student_loan_days,
            "staff_loan_days": cfg.staff_loan_days,
        }

    @app.get("/books", summary="List and search books in catalog")
    def list_books(
        query: Optional[str] = Query(None, description="Search term for title or author"),
        genre: Optional[str] = Query(None, description="Filter by genre"),
        svc: LibraryService = Depends(get_service),
    ) -> List[Dict[str, Any]]:
        # Uses lazy generator iter_catalog if no query, or search
        if not query:
            return [b.to_dict() for b in svc.iter_catalog(genre=genre)]
        return [b.to_dict() for b in svc.search_books(query=query, genre=genre)]

    @app.post("/books", status_code=status.HTTP_201_CREATED, summary="Add a new book to catalog")
    def add_book(
        req: AddBookRequest, svc: LibraryService = Depends(get_service)
    ) -> Dict[str, Any]:
        book = svc.add_book(
            title=req.title,
            author=req.author,
            isbn=req.isbn,
            genre=req.genre,
            total_copies=req.copies,
        )
        return {"message": "Book added successfully", "book": book.to_dict()}

    @app.post("/members", status_code=status.HTTP_201_CREATED, summary="Register a library member")
    def register_member(
        req: AddMemberRequest, svc: LibraryService = Depends(get_service)
    ) -> Dict[str, Any]:
        member = svc.register_member(
            member_id=req.member_id,
            name=req.name,
            email=req.email,
            member_type=req.member_type,
        )
        return {"message": "Member registered successfully", "member": member.to_dict()}

    @app.get("/members/{member_id}", summary="Get member details and active borrowing status")
    def get_member(
        member_id: str, svc: LibraryService = Depends(get_service)
    ) -> Dict[str, Any]:
        return svc.get_member_status(member_id)

    @app.post("/borrow", summary="Borrow a book")
    def borrow_book(
        req: BorrowBookRequest, svc: LibraryService = Depends(get_service)
    ) -> Dict[str, Any]:
        loan = svc.borrow_book(
            member_id=req.member_id,
            isbn=req.isbn,
            borrow_date=req.borrow_date,
        )
        return {"message": "Book borrowed successfully", "loan": loan.to_dict()}

    @app.post("/return", summary="Return a borrowed book")
    def return_book(
        req: ReturnBookRequest, svc: LibraryService = Depends(get_service)
    ) -> Dict[str, Any]:
        result = svc.return_book(
            member_id=req.member_id,
            isbn=req.isbn,
            return_date=req.return_date,
            fine_paid=req.fine_paid,
        )
        return {"message": "Book returned successfully", "result": result}

    @app.get("/loans/overdue", summary="List all currently overdue book loans (lazy stream)")
    def list_overdue(
        as_of: Optional[date] = Query(None, description="Reference date YYYY-MM-DD"),
        svc: LibraryService = Depends(get_service),
    ) -> List[Dict[str, Any]]:
        return list(svc.iter_overdue_loans(as_of_date=as_of))

    return app


# Default ASGI application instance for uvicorn
app = create_app()
