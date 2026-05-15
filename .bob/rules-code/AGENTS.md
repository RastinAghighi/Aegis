# Code Mode Rules (Non-Obvious Only)

## Critical Implementation Patterns

### Database Operations
- Database path is **CWD-relative** (`.aegis/findings.db`), not project-root-relative
- Use [`database.py:_db_path()`](../../Aegis/database.py:23) to get correct path
- Must call `init_db()` before any database operations

### Pattern Matching
- [`pattern_matcher.find_all()`](../../Aegis/scanner/pattern_matcher.py:25) returns **1-indexed** line numbers
- Evidence model expects 1-indexed lines, matching this behavior
- Do NOT subtract 1 when creating Evidence objects from pattern matches

### Import Requirements
- ALL Python files must start with `from __future__ import annotations`
- This enables forward references for type hints (Python 3.11+ requirement)

### Rule Implementation
- Rules inherit from [`Rule`](../../Aegis/rules/base.py:12) ABC
- Must implement `check(sources: Iterable[SourceFile]) -> Iterable[Finding]`
- Rule files named: `{id}_{name}.py` (e.g., `ac_1_access_control.py`)
- Each rule must define: `id`, `title`, `severity`, `cfr`, `remediation`

### MCP Server
- Uses **stdio transport only** (not TCP despite `--port` parameter)
- Port parameter in [`serve_mcp()`](../../Aegis/cli.py:62) is reserved for future use
- Implement using `mcp` Python SDK with stdio

### CLI Commands
- All three commands ([`scan`](../../Aegis/cli.py:33), [`report`](../../Aegis/cli.py:54), [`serve-mcp`](../../Aegis/cli.py:62)) are currently stubs
- They print "not implemented" and exit with code 0
- Tests verify this stub behavior, not actual functionality

### Dashboard API
- CORS hardcoded to `http://localhost:5173` in [`api/main.py:16`](../../Aegis/api/main.py:16)
- Must update this if dashboard runs on different port
- FastAPI app uses standard middleware setup

## Testing Patterns

- Test files must be named `test_*.py` in `tests/` directory
- Async tests use `asyncio_mode = "auto"` (no explicit markers needed)
- CLI tests use `click.testing.CliRunner` for command invocation
- Tests verify stub behavior (exit code 0, "not implemented" in output)

## Code Style Enforcement

- Line length: 100 characters (enforced by ruff)
- Ruff rules: E, F, W, I, B, UP (E501 ignored for line length)
- mypy: `strict = false`, `ignore_missing_imports = true`
- Use `ruff format .` before committing (not black)