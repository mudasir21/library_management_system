# HCLTech Library Management System

A Python library-management application with two ways to use the same business
logic: a command-line interface (CLI) and a REST API. It stores books, members,
and loans in SQLite.

## Features

- Add, browse, filter, and search books by title, author, or genre.
- Register students, staff, and faculty members.
- Borrow and return books, with inventory and member-loan limits enforced.
- View member details, active loans, loan history, and pending overdue fines.
- List overdue loans and calculate fines using configurable daily rates.
- Apply deterministic library rules based on an employee ID, including allowed
  genres and student/staff borrowing limits.
- Use the same service layer through either the CLI or FastAPI endpoints.
- Persist data in SQLite and write application/audit activity to a log file.

## Requirements

- Python 3.10 or newer.
- pip.

All runtime and development/test dependencies are listed in the single
[`requirements.txt`](requirements.txt) file.

## Install

From the repository root, create and activate a virtual environment, then
install the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, use the environment's
interpreter directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run the CLI

Run commands from the repository root so Python can find the `library` package:

```powershell
python -m library.delivery.cli --help
python -m library.delivery.cli config
```

The `config` command shows the genres allowed for the selected employee ID.
Choose one of those genres when adding a book. The global `--employee-id` and
`--db-path` options go before the subcommand.

Example workflow:

```powershell
python -m library.delivery.cli add-book --title "Example Book" --author "A. Author" --isbn 9780306406157 --genre Fiction --copies 2
python -m library.delivery.cli add-member --id STU-1001 --name "Sam Student" --email sam@example.com --type student
python -m library.delivery.cli list-books
python -m library.delivery.cli borrow --member-id STU-1001 --isbn 9780306406157
python -m library.delivery.cli member-details --id STU-1001
python -m library.delivery.cli list-overdue
python -m library.delivery.cli return --member-id STU-1001 --isbn 9780306406157
```

Use `--query` and `--genre` with `list-books` to filter results. Use
`--as-of YYYY-MM-DD` with `list-overdue` to calculate overdue status for a
specific date. Add `--paid` to `return` when collecting an overdue fine.

For an isolated database, pass a path before the command:

```powershell
python -m library.delivery.cli --db-path .\test-library.db add-book --title "Example Book" --author "A. Author" --isbn 9780306406157 --genre Fiction
```

## Run the REST API

Start the API server from the repository root:

```powershell
python -m uvicorn library.delivery.api:app --reload
```

Open these URLs in a browser:

- Welcome message: <http://127.0.0.1:8000/>
- Interactive API documentation: <http://127.0.0.1:8000/docs>
- Alternative API documentation: <http://127.0.0.1:8000/redoc>

### API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/config` | Show the active library rules |
| `GET` | `/books` | List/search books; optional `query` and `genre` parameters |
| `POST` | `/books` | Add a book |
| `POST` | `/members` | Register a member |
| `GET` | `/members/{member_id}` | Read member status and active loans |
| `POST` | `/borrow` | Borrow a book |
| `POST` | `/return` | Return a book and calculate any fine |
| `GET` | `/loans/overdue` | List overdue loans; optional `as_of` date |

The `/docs` page lets you inspect request schemas and try endpoints without
writing a separate API client.

## Configuration and data files

The defaults are `HCL10001` for the employee ID, `library.db` for the SQLite
database, and `library.log` for the log file. These files are created relative
to the working directory when the application runs.

Configuration can be supplied through environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `LIBRARY_EMPLOYEE_ID` | `HCL10001` | Employee ID used to derive personalized genres and rules |
| `LIBRARY_DB_PATH` | `library.db` | SQLite database file path |
| `LIBRARY_LOG_PATH` | `library.log` | Application log file path |

CLI `--employee-id` and `--db-path` options override their corresponding
environment variables. The generated genres, student/staff limits, and daily
fine rate are deterministic for a given employee ID. Faculty use a borrowing
limit of 10; member loan durations are 14 days for students, 28 for staff, and
60 for faculty.

## Application workflow and architecture

1. A request enters through either `library.delivery.cli` or the FastAPI app in
   `library.delivery.api`.
2. The delivery layer parses input and delegates to `LibraryService`; business
   rules are kept out of the CLI and HTTP route handlers.
3. `LibraryService` validates input and coordinates book, member, and loan
   workflows through repository interfaces.
4. SQLite repository implementations persist records through a shared
   `DatabaseManager`; transactions commit successful changes and roll back on
   errors.
5. Domain entities (`Book`, `Member`, and `Loan`) represent application data
   and enforce domain behavior. The API translates domain errors into
   appropriate HTTP responses, while the CLI prints readable messages.

```text
library/
├── delivery/        # CLI and FastAPI adapters
├── domain/          # Book, member, and loan entities
├── infrastructure/  # SQLite database, repositories, and logging
├── interfaces/      # Repository contracts
├── service/         # Library use cases and business rules
├── config.py        # Personalized rules and application settings
├── context_managers.py
├── decorators.py
├── exceptions.py
└── validators.py
```

The project also demonstrates object-oriented design, repository/factory
patterns, custom exceptions, validators, decorators for audit logging, lazy
iterators for catalog/overdue listings, and transaction context managers.

## Tests

`pytest` and `httpx` are included in `requirements.txt` for development and API
testing. There are currently no test files in the repository. Run the suite
after adding tests with:

```powershell
python -m pytest
```
