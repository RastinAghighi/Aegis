# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Build & Test Commands

```bash
# Setup (REQUIRED before first use)
python scripts/setup.py              # Installs Python package + dashboard deps
python scripts/setup.py --check      # Verify toolchain only
python scripts/setup.py --no-dash    # Skip dashboard install

# Python package (editable install)
pip install -e .[dev]

# Run tests
pytest                               # All tests
pytest tests/test_cli.py            # Single test file

# Linting
ruff check .                        # Lint Python code
ruff format .                       # Format Python code
mypy Aegis/                         # Type check

# Dashboard (from dashboard/ directory)
cd dashboard && npm run dev         # Dev server on :5173
cd dashboard && npm run build       # Production build
cd dashboard && npm run lint        # ESLint

# Demo stack
docker compose up                   # Start patient-portal + dashboard + postgres
docker compose up -d                # Detached mode
```

## Critical Non-Obvious Patterns

### Database Location
- Findings database is created at `.aegis/findings.db` **relative to CWD**, not project root
- Created automatically by [`database.py:_db_path()`](Aegis/database.py:23)

### CLI Commands Are Stubs
- All three commands ([`scan`](Aegis/cli.py:33), [`report`](Aegis/cli.py:54), [`serve-mcp`](Aegis/cli.py:62)) print "not implemented" and exit 0
- Tests verify stub behavior, not actual functionality

### Pattern Matcher Returns 1-Indexed Lines
- [`pattern_matcher.find_all()`](Aegis/scanner/pattern_matcher.py:25) returns **1-indexed** line numbers
- This matches Evidence model expectations but differs from typical 0-indexed Python

### MCP Server Uses stdio Transport
- Despite `--port` parameter, MCP server uses stdio (not TCP)
- Port parameter reserved for future TCP transport

### Demo Patient Portal Vulnerabilities
- Hardcoded credentials: `admin/admin` in [`routes/auth.js:19`](demo/patient-portal/routes/auth.js:19)
- Missing auth on [`GET /patients/:id`](demo/patient-portal/routes/patients.js:24) (deliberate HIPAA violation)
- These are intentional for scanner testing

### Dashboard CORS Restriction
- FastAPI backend hardcoded to allow only `http://localhost:5173` in [`api/main.py:16`](Aegis/api/main.py:16)
- Change this if running dashboard on different port

## Code Style (from pyproject.toml)

- Line length: 100 characters
- Python 3.11+ required (uses `from __future__ import annotations`)
- Ruff linting: E, F, W, I, B, UP rules enabled (E501 ignored)
- Type hints: mypy with `strict = false`, `ignore_missing_imports = true`
- Test files: `test_*.py` in `tests/` directory
- Async tests: `asyncio_mode = "auto"` for pytest

## Project Structure Quirks

- Python package name is `aegis` (lowercase) but directory is `Aegis/` (capitalized)
- Three separate Node.js projects: `dashboard/`, `demo/patient-portal/`, each with own package.json
- `bob_sessions/` directory for Bob hackathon session data (not part of package)
- Rules in `Aegis/rules/` follow naming: `{id}_{name}.py` (e.g., `ac_1_access_control.py`)