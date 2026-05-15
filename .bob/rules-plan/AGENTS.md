# Plan Mode Rules (Non-Obvious Only)

## Architectural Constraints

### Database Location Dependency
- Database created at `.aegis/findings.db` **relative to CWD**, not project root
- This creates coupling between command execution location and data persistence
- See [`database.py:_db_path()`](../../Aegis/database.py:23)
- Consider: Should database be project-root-relative instead?

### CLI Stub Architecture
- All three commands ([`scan`](../../Aegis/cli.py:33), [`report`](../../Aegis/cli.py:54), [`serve-mcp`](../../Aegis/cli.py:62)) are stubs
- Exit with code 0 despite not being implemented
- Tests verify stub behavior, creating technical debt for real implementation
- Planning implementations must account for this test structure

### MCP Transport Decision
- MCP server uses **stdio transport only** (not TCP)
- Port parameter exists but is unused (reserved for future)
- This architectural decision affects how Bob integrates with Aegis
- Any TCP implementation would require backward compatibility

### Pattern Matcher Line Indexing
- [`pattern_matcher.find_all()`](../../Aegis/scanner/pattern_matcher.py:25) returns **1-indexed** lines
- Differs from Python's typical 0-indexed conventions
- This decision propagates through Evidence model and all rules
- Changing this would require coordinated updates across multiple components

## Component Coupling

### Dual Package Structure
- Python package (`Aegis/`) + separate Node.js projects (`dashboard/`, `demo/patient-portal/`)
- Each has independent dependency management
- Setup script ([`scripts/setup.py`](../../scripts/setup.py)) coordinates installation
- Changes to one component don't automatically propagate to others

### Dashboard CORS Hardcoding
- FastAPI backend hardcoded to `http://localhost:5173` in [`api/main.py:16`](../../Aegis/api/main.py:16)
- Not configurable via environment variables
- Creates tight coupling between API and dashboard deployment
- Any production deployment requires source code changes

### Rule Implementation Pattern
- Rules inherit from [`Rule`](../../Aegis/rules/base.py:12) ABC
- Each rule must define: `id`, `title`, `severity`, `cfr`, `remediation`
- File naming convention: `{id}_{name}.py` (e.g., `ac_1_access_control.py`)
- Adding new rules requires following this exact pattern

## Demo Architecture

### Intentional Vulnerabilities
- Patient portal contains deliberate HIPAA violations for testing:
  - Hardcoded `admin/admin` in [`routes/auth.js:19`](../../demo/patient-portal/routes/auth.js:19)
  - Missing auth on [`GET /patients/:id`](../../demo/patient-portal/routes/patients.js:24)
- These are test fixtures, not bugs
- Scanner rules must detect these specific patterns

### Docker Compose Stack
- Three services: `patient-portal-db`, `patient-portal`, `dashboard`
- Patient portal depends on database health check
- Dashboard volume-mounts source for hot reload
- All services use hardcoded dev credentials (not production-ready)

## Import Requirements
- ALL Python files must start with `from __future__ import annotations`
- Required for Python 3.11+ forward reference type hints
- This is a project-wide convention enforced by code style