# Ask Mode Rules (Non-Obvious Only)

## Project Structure Context

### Package Naming Inconsistency
- Python package name is `aegis` (lowercase) but directory is `Aegis/` (capitalized)
- Import as `from aegis.models import Finding`, not `from Aegis.models`
- This is intentional for Python package naming conventions

### Multiple Node.js Projects
- Three separate Node.js projects with independent `package.json`:
  - `dashboard/` - React + Vite + shadcn/ui dashboard
  - `demo/patient-portal/` - Express.js vulnerable demo app
  - Each has own dependencies and must be installed separately

### Bob Sessions Directory
- `bob_sessions/` contains Bob hackathon session data
- Not part of the Python package (excluded in [`pyproject.toml:56`](../../pyproject.toml:56))
- Used for development/demo purposes only

## Architecture Context

### CLI Commands Are Stubs
- All three commands ([`scan`](../../Aegis/cli.py:33), [`report`](../../Aegis/cli.py:54), [`serve-mcp`](../../Aegis/cli.py:62)) print "not implemented"
- Exit with code 0 (success) despite not being implemented
- This is intentional for hackathon demo - tests verify stub behavior

### Database Location
- Findings database created at `.aegis/findings.db` **relative to CWD**, not project root
- This means database location changes based on where commands are run
- See [`database.py:_db_path()`](../../Aegis/database.py:23) for implementation

### Demo Vulnerabilities Are Intentional
- Patient portal in `demo/patient-portal/` contains deliberate HIPAA violations:
  - Hardcoded `admin/admin` credentials in [`routes/auth.js:19`](../../demo/patient-portal/routes/auth.js:19)
  - Missing auth on [`GET /patients/:id`](../../demo/patient-portal/routes/patients.js:24)
  - These are test cases for the scanner, not bugs to fix

### MCP Server Transport
- Despite `--port` parameter, MCP server uses **stdio transport** (not TCP)
- Port parameter in [`serve_mcp()`](../../Aegis/cli.py:62) reserved for future TCP support
- This is a design decision for local Bob integration

## Code Organization

### Rule Naming Convention
- Rules in `Aegis/rules/` follow pattern: `{id}_{name}.py`
- Example: `ac_1_access_control.py` for rule AC-1
- ID matches HIPAA control identifier

### Pattern Matcher Line Numbering
- [`pattern_matcher.find_all()`](../../Aegis/scanner/pattern_matcher.py:25) returns **1-indexed** line numbers
- This differs from typical Python 0-indexed conventions
- Matches Evidence model expectations for line references

### Dashboard CORS Configuration
- FastAPI backend only allows `http://localhost:5173` in [`api/main.py:16`](../../Aegis/api/main.py:16)
- Hardcoded for development - not configurable via environment
- Must modify source if running dashboard on different port