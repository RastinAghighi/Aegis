# Aegis

HIPAA compliance code auditor built for the IBM Bob Hackathon.

<TO FILL: tagline / one-line elevator pitch>

## What it does

<TO FILL: short paragraph describing what Aegis does — scans codebases for HIPAA violations, produces evidence-based reports with CFR citations, exposes findings via MCP so Bob can reason about them>

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system design.

High level:
- **Scanner** (`aegis/scanner/`) — tree-sitter parses code, pattern matchers extract structural facts
- **Rules** (`aegis/rules/`) — one rule per HIPAA control (AC-1, AC-2, AC-3, AU-1, EN-1, TR-1, IN-1)
- **Reporter** (`aegis/reporter/`) — PDF (ReportLab) and JSON exports with CFR citations
- **MCP Server** (`aegis/mcp_server.py`) — Bob talks to Aegis through MCP tools
- **API** (`aegis/api/`) — FastAPI backend for the dashboard
- **Dashboard** (`dashboard/`) — React + Vite + shadcn/ui

## Quick start

```bash
# 1. Install Python package and dashboard deps
python scripts/setup.py

# 2. Start the demo stack (vulnerable Patient Portal + dashboard)
docker compose up

# 3. Scan the demo
aegis scan demo/patient-portal

# 4. Generate a PDF report
aegis report --format pdf --out findings.pdf

# 5. Launch MCP server (Bob connects here)
aegis serve-mcp
```

## Demo target

`demo/patient-portal/` is a deliberately non-compliant Express.js + PostgreSQL
healthcare API used to exercise the scanner. It contains 10 seeded HIPAA
violations across access control, audit logging, encryption, transmission
security, and integrity.

<TO FILL: link to live demo URL if hosted>

## HIPAA rules covered

See [docs/HIPAA-RULES.md](docs/HIPAA-RULES.md) for the rule catalog with full
45 CFR §164 citations.

| ID    | Control                                | CFR                  |
|-------|----------------------------------------|----------------------|
| AC-1  | Access Control — auth required         | §164.312(a)(1)       |
| AC-2  | Session timeout                        | §164.312(a)(2)(iii)  |
| AC-3  | Authentication strength                | §164.312(d)          |
| AU-1  | Audit logging                          | §164.312(b)          |
| EN-1  | Encryption at rest                     | §164.312(a)(2)(iv)   |
| TR-1  | Transmission security                  | §164.312(e)(1)       |
| IN-1  | Integrity controls                     | §164.312(c)(1)       |

## Demo script

See [docs/DEMO-SCRIPT.md](docs/DEMO-SCRIPT.md) for the judging walkthrough.

## Project layout

<TO FILL: prose description of the layout, or `tree -L 2` output>

## Development

<TO FILL: how to run tests, lint, etc.>

```bash
pytest
```

## License

MIT. See [LICENSE](LICENSE).

## Authors

<TO FILL>
