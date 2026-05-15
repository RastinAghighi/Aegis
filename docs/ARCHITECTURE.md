# Aegis Architecture

**Version:** 0.1.0  
**Last Updated:** 2026-05-15  
**Target Audience:** Hackathon judges, technical reviewers, future contributors

---

## Executive Summary

Aegis is a HIPAA compliance code auditor that combines **deterministic static analysis** with **LLM-powered contextual reasoning**. The system performs surgical, per-file detection of HIPAA Security Rule violations using tree-sitter AST parsing, then exposes findings via MCP (Model Context Protocol) so Bob—an AI agent in Auditor mode—can perform cross-file analysis, trace PHI data flows, and generate remediation pull requests.

**Key Innovation:** The architecture cleanly separates what machines do best (fast, exhaustive pattern matching) from what LLMs excel at (understanding context, reasoning about data flow across module boundaries, generating human-readable explanations).

---

## 1. Component Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER / DEVELOPER                                │
└────────┬────────────────────────────────────────────────────┬────────────┘
         │                                                     │
         │ CLI commands                                        │ Browser
         │ (aegis scan/report)                                 │ (localhost:5173)
         │                                                     │
         ▼                                                     ▼
┌─────────────────────┐                            ┌──────────────────────┐
│   Aegis CLI         │                            │  React Dashboard     │
│   (cli.py)          │                            │  (Vite + shadcn/ui)  │
│                     │                            │                      │
│  • scan             │                            │  • Findings table    │
│  • report           │                            │  • Severity filters  │
│  • serve-mcp        │                            │  • Evidence viewer   │
└──────┬──────────────┘                            └──────────┬───────────┘
       │                                                      │
       │ invokes                                              │ HTTP
       │                                                      │
       ▼                                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AEGIS CORE ENGINE                                │
│                                                                          │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────────────┐  │
│  │   Scanner    │─────▶│ Rules Engine │─────▶│   Database           │  │
│  │              │      │              │      │   (.aegis/           │  │
│  │ • walk()     │      │ • AC-1..IN-1 │      │    findings.db)      │  │
│  │ • parse()    │      │ • check()    │      │                      │  │
│  │ • tree-sitter│      │ • yield      │      │ • FindingRow         │  │
│  │   AST        │      │   Finding    │      │ • ReportRow          │  │
│  └──────────────┘      └──────────────┘      └──────────┬───────────┘  │
│                                                          │              │
│                                                          │ queries      │
│  ┌──────────────────────────────────────────────────────▼───────────┐  │
│  │                    FastAPI Backend                               │  │
│  │                    (api/main.py)                                 │  │
│  │                                                                  │  │
│  │  GET /findings?severity=&rule_id=                               │  │
│  │  GET /findings/{id}                                             │  │
│  │  GET /reports                                                   │  │
│  │  POST /scan                                                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Reporter                                      │  │
│  │                    (reporter/)                                   │  │
│  │                                                                  │  │
│  │  • pdf.py      → ReportLab PDF with CFR citations               │  │
│  │  • json_export → Structured JSON for CI/CD pipelines            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  │ stdio transport
                                  │ (MCP protocol)
                                  ▼
                        ┌──────────────────────┐
                        │   MCP Server         │
                        │   (mcp_server.py)    │
                        │                      │
                        │  Tools exposed:      │
                        │  • list_findings()   │
                        │  • get_finding()     │
                        │  • explain_rule()    │
                        │  • run_scan()        │
                        │  • generate_report() │
                        └──────────┬───────────┘
                                   │
                                   │ MCP protocol
                                   │ (JSON-RPC over stdio)
                                   ▼
                        ┌──────────────────────┐
                        │   Bob (Auditor Mode) │
                        │                      │
                        │  • Cross-file PHI    │
                        │    flow analysis     │
                        │  • Second-order      │
                        │    violations        │
                        │  • Remediation PRs   │
                        │  • Contextual        │
                        │    explanations      │
                        └──────────────────────┘
                                   │
                                   │ analyzes
                                   ▼
                        ┌──────────────────────┐
                        │  Demo Patient Portal │
                        │  (Express + Postgres)│
                        │                      │
                        │  Seeded violations:  │
                        │  • Hardcoded creds   │
                        │  • Missing auth      │
                        │  • No encryption     │
                        │  • Weak sessions     │
                        └──────────────────────┘
```

### Component Responsibilities

#### **Scanner** ([`Aegis/scanner/`](../Aegis/scanner/))
- **Purpose:** File discovery, language detection, AST parsing
- **Key Files:**
  - [`base.py`](../Aegis/scanner/base.py) — `Scanner` ABC, `SourceFile` dataclass
  - [`tree_sitter.py`](../Aegis/scanner/tree_sitter.py) — Tree-sitter parser wrapper for JS/TS
  - [`pattern_matcher.py`](../Aegis/scanner/pattern_matcher.py) — Regex-based fallback for SQL/JSON
- **Outputs:** `Iterable[SourceFile]` with parsed AST trees
- **Exclusions:** `node_modules/`, `.git/`, `dist/`, `build/`, `.venv/`, `__pycache__/`

#### **Rules Engine** ([`Aegis/rules/`](../Aegis/rules/))
- **Purpose:** Per-file HIPAA violation detection
- **Architecture:** Each rule is a subclass of [`Rule`](../Aegis/rules/base.py:12) ABC
- **Rules Implemented:**
  - [`ac_1_access_control.py`](../Aegis/rules/ac_1_access_control.py) — Auth middleware checks
  - [`ac_2_session_timeout.py`](../Aegis/rules/ac_2_session_timeout.py) — Session `maxAge` validation
  - [`ac_3_authentication.py`](../Aegis/rules/ac_3_authentication.py) — Hardcoded credentials, weak auth
  - [`au_1_audit_logs.py`](../Aegis/rules/au_1_audit_logs.py) — PHI access logging
  - [`en_1_encryption.py`](../Aegis/rules/en_1_encryption.py) — Encryption at rest
  - [`tr_1_transmission.py`](../Aegis/rules/tr_1_transmission.py) — TLS/HTTPS enforcement
  - [`in_1_integrity.py`](../Aegis/rules/in_1_integrity.py) — Mass-update detection
- **Contract:** `check(sources: Iterable[SourceFile]) -> Iterable[Finding]`
- **Outputs:** [`Finding`](../Aegis/models.py:40) objects with [`Evidence`](../Aegis/models.py:30) and [`CFRCitation`](../Aegis/models.py:19)

#### **Database** ([`Aegis/database.py`](../Aegis/database.py))
- **Technology:** SQLAlchemy + SQLite
- **Location:** `.aegis/findings.db` (relative to CWD, **not** project root)
- **Schema:**
  - `findings` table — denormalized finding storage with JSON CFR column
  - `reports` table — scan metadata + finding ID references
- **Critical Detail:** Database path is CWD-relative (line 24), created automatically on first use

#### **Reporter** ([`Aegis/reporter/`](../Aegis/reporter/))
- **Purpose:** Export findings to human-readable formats
- **Formats:**
  - **PDF** ([`pdf.py`](../Aegis/reporter/pdf.py)) — ReportLab-based report with:
    - Cover page (target, timestamp, severity counts)
    - Per-rule sections with full CFR text
    - Evidence blocks with syntax-highlighted snippets
  - **JSON** ([`json_export.py`](../Aegis/reporter/json_export.py)) — Machine-readable for CI/CD
- **Input:** [`Report`](../Aegis/models.py:53) model (collection of findings)

#### **MCP Server** ([`Aegis/mcp_server.py`](../Aegis/mcp_server.py))
- **Purpose:** Expose Aegis capabilities to Bob via Model Context Protocol
- **Transport:** stdio (JSON-RPC over stdin/stdout)
- **Tools Exposed:**
  - `list_findings(severity?, rule_id?)` — Query findings with filters
  - `get_finding(finding_id)` — Retrieve full evidence + CFR text
  - `explain_rule(rule_id)` — Return CFR citation + remediation guidance
  - `run_scan(path)` — Trigger scan and persist findings
  - `generate_report(format, path)` — Emit PDF/JSON report
- **Why stdio?** Bob runs locally; stdio is simpler than TCP for local IPC
- **Future:** `--port` parameter reserved for TCP transport (multi-user scenarios)

#### **FastAPI Backend** ([`Aegis/api/main.py`](../Aegis/api/main.py))
- **Purpose:** HTTP API for React dashboard
- **CORS:** Hardcoded to `http://localhost:5173` (Vite dev server)
- **Endpoints:**
  - `GET /findings?severity=&rule_id=` — Filtered finding list
  - `GET /findings/{id}` — Single finding detail
  - `GET /reports` — Scan history
  - `POST /scan` — Trigger new scan
- **Authentication:** None (local dev tool; production would add auth)

#### **React Dashboard** ([`dashboard/`](../dashboard/))
- **Technology:** Vite + React + TypeScript + shadcn/ui + Tailwind
- **Pages:**
  - [`Overview.tsx`](../dashboard/src/pages/Overview.tsx) — Severity distribution, recent scans
  - [`Findings.tsx`](../dashboard/src/pages/Findings.tsx) — Filterable table, evidence viewer
  - [`Reports.tsx`](../dashboard/src/pages/Reports.tsx) — Report history, download links
- **API Client:** [`lib/api.ts`](../dashboard/src/lib/api.ts) — Axios wrapper for FastAPI backend

#### **Demo Patient Portal** ([`demo/patient-portal/`](../demo/patient-portal/))
- **Purpose:** Deliberately vulnerable Express.js app for scanner testing
- **Technology:** Express + Sequelize + PostgreSQL
- **Seeded Violations:**
  - **AC-3:** Hardcoded `admin/admin` credentials ([`routes/auth.js:19`](../demo/patient-portal/routes/auth.js:19))
  - **AC-1:** Missing auth on `GET /patients/:id` ([`routes/patients.js:24`](../demo/patient-portal/routes/patients.js:24))
  - **AC-2:** 24-hour session timeout (should be ≤15 min)
  - **EN-1:** Plaintext SSN storage in Patient model
  - **AU-1:** No audit log on patient detail retrieval
  - **TR-1:** `ssl: false` in database config
  - **IN-1:** Mass-update without scoped predicates
- **Why Deliberate?** Provides known-good test cases for rule validation

---

## 2. Data Flow

### 2.1 Scan Execution Flow

```
User runs: aegis scan demo/patient-portal
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 1. CLI (cli.py:scan)                                       │
│    • Parse target path                                     │
│    • Initialize Scanner(target)                            │
│    • Initialize Database                                   │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 2. Scanner.walk()                                          │
│    • Recursively traverse target directory                 │
│    • Skip excluded paths (node_modules, .git, etc.)        │
│    • Detect language from file extension                   │
│    • Read file content                                     │
│    • Yield SourceFile(path, language, text)                │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 3. Scanner.parse(SourceFile)                               │
│    • If JS/TS: tree-sitter AST parsing                     │
│    • If SQL/JSON: pattern_matcher fallback                 │
│    • Attach parsed tree to SourceFile.tree                 │
│    • Return enriched SourceFile                            │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 4. Rules Engine Evaluation                                 │
│    For each Rule in [AC-1, AC-2, AC-3, AU-1, EN-1, TR-1,  │
│                      IN-1]:                                │
│      • rule.check(sources) → Iterable[Finding]             │
│      • Rule queries AST nodes (e.g., route handlers)       │
│      • Pattern matching on syntax (e.g., hardcoded creds)  │
│      • Yield Finding with Evidence (file, line, snippet)   │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 5. Database Persistence                                    │
│    • Insert each Finding into findings table               │
│    • Create ReportRow with finding IDs                     │
│    • Commit transaction                                    │
│    • Database at .aegis/findings.db (CWD-relative)         │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 6. CLI Output                                              │
│    • Print summary: "Found 12 violations (3 CRITICAL)"     │
│    • Suggest: "Run 'aegis report --format pdf' to export" │
└────────────────────────────────────────────────────────────┘
```

### 2.2 Report Generation Flow

```
User runs: aegis report --format pdf --out findings.pdf
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 1. CLI (cli.py:report)                                     │
│    • Query latest ReportRow from database                  │
│    • Fetch all associated FindingRows                      │
│    • Construct Report model                                │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 2. Reporter (reporter/pdf.py or json_export.py)            │
│    • Group findings by rule_id                             │
│    • Sort by severity (CRITICAL → LOW)                     │
│    • For PDF:                                              │
│      - ReportLab SimpleDocTemplate                         │
│      - Cover page with severity distribution chart         │
│      - Per-rule sections with CFR verbatim text            │
│      - Evidence blocks with syntax highlighting            │
│    • For JSON:                                             │
│      - Serialize Report model to JSON                      │
│      - Include full CFR citations                          │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 3. File Output                                             │
│    • Write to specified path (findings.pdf / findings.json)│
│    • Print: "Report written to findings.pdf"               │
└────────────────────────────────────────────────────────────┘
```

### 2.3 Bob Integration Flow (MCP)

```
Bob in Auditor mode receives task: "Review HIPAA compliance for patient-portal"
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 1. Bob connects to MCP server                              │
│    • User runs: aegis serve-mcp                            │
│    • Bob establishes stdio connection                      │
│    • MCP handshake (protocol version negotiation)          │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 2. Bob calls: run_scan("demo/patient-portal")             │
│    • MCP server invokes Scanner + Rules Engine             │
│    • Findings persisted to database                        │
│    • Returns: { scan_id, finding_count }                   │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 3. Bob calls: list_findings(severity="CRITICAL")           │
│    • MCP server queries database                           │
│    • Returns: [{ id, rule_id, file, line, snippet }, ...]  │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 4. Bob performs cross-file analysis                        │
│    • Reads full repo context (not just snippets)           │
│    • Traces PHI flow: Patient model → routes → responses   │
│    • Identifies second-order violations:                   │
│      - "auth.js exports requireAuth but patients.js        │
│         doesn't import it for GET /:id"                    │
│      - "Patient.ssn is plaintext but never encrypted       │
│         before database write"                             │
│    • Reasons about intent vs. implementation               │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 5. Bob calls: explain_rule("AC-1")                         │
│    • MCP server returns CFR citation + remediation         │
│    • Bob uses this to generate PR description              │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────┐
│ 6. Bob generates remediation PR                            │
│    • Creates branch: fix/hipaa-ac-1-patients-auth          │
│    • Applies fix: Add requireAuth to GET /patients/:id     │
│    • Writes PR description with CFR citation               │
│    • Submits PR for human review                           │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Cross-File Analysis Split

### 3.1 What Aegis Does (Deterministic, Per-File)

**Aegis operates on individual files in isolation.** It uses tree-sitter AST parsing and pattern matching to detect violations that can be determined from a single file's syntax tree.

#### Examples of Aegis-Detected Violations:

1. **AC-3 (Hardcoded Credentials)** — [`auth.js:19`](../demo/patient-portal/routes/auth.js:19)
   ```javascript
   if (username === 'admin' && password === 'admin') { ... }
   ```
   - **Detection:** AST query for `BinaryExpression` with string literal comparisons
   - **No cross-file context needed:** Violation is self-contained

2. **AC-2 (Session Timeout)** — `middleware/session.js`
   ```javascript
   session({ cookie: { maxAge: 86400000 } })  // 24 hours
   ```
   - **Detection:** AST query for `session()` call, extract `maxAge` value
   - **Validation:** `maxAge > 900000` (15 minutes) → violation

3. **EN-1 (Plaintext PHI)** — `models/Patient.js`
   ```javascript
   ssn: { type: DataTypes.STRING }  // No encryption
   ```
   - **Detection:** AST query for Sequelize model definitions, check for encryption wrappers
   - **Pattern:** `DataTypes.STRING` without `get()`/`set()` hooks → violation

4. **TR-1 (Insecure Transmission)** — `config/database.js`
   ```javascript
   ssl: false
   ```
   - **Detection:** AST query for object literals with `ssl` property
   - **Validation:** `ssl === false` → violation

**Key Limitation:** Aegis **cannot** determine if a route handler actually uses authentication middleware without analyzing the middleware chain across files.

### 3.2 What Bob Does (Contextual, Cross-File)

**Bob operates with full repository context.** It reads multiple files, understands import/export relationships, and traces data flow across module boundaries.

#### Examples of Bob-Detected Violations:

1. **AC-1 (Missing Auth Middleware)** — [`patients.js:24`](../demo/patient-portal/routes/patients.js:24)
   ```javascript
   // patients.js
   router.get('/:id', async (req, res) => { ... })  // No requireAuth
   ```
   - **Aegis sees:** Route handler definition (syntactically valid)
   - **Bob sees:**
     - `auth.js` exports `requireAuth` function
     - `patients.js` imports `requireAuth` but doesn't use it on line 24
     - Other routes in same file (`GET /`, `POST /`) **do** use `requireAuth`
     - **Conclusion:** Inconsistent auth enforcement → violation

2. **AU-1 (Missing Audit Log)** — `patients.js:24-27`
   ```javascript
   router.get('/:id', async (req, res) => {
     const patient = await Patient.findByPk(req.params.id);
     res.json(patient);  // No AuditLog.create()
   })
   ```
   - **Aegis sees:** `Patient.findByPk()` call (syntactically valid)
   - **Bob sees:**
     - `GET /` route (line 9) **does** call `AuditLog.create()` after `Patient.findAll()`
     - `GET /:id` route (line 24) **does not** call `AuditLog.create()`
     - **Conclusion:** Inconsistent audit logging → violation

3. **PHI Data Flow Tracing**
   ```javascript
   // models/Patient.js
   ssn: { type: DataTypes.STRING }  // Plaintext
   
   // routes/patients.js
   const patient = await Patient.findByPk(id);
   res.json(patient);  // SSN exposed in response
   ```
   - **Aegis sees:** Two separate violations (plaintext storage + no encryption)
   - **Bob sees:**
     - SSN is stored plaintext in database
     - SSN is read from database without decryption
     - SSN is serialized to JSON response without redaction
     - **Conclusion:** End-to-end PHI exposure → compound violation

4. **Second-Order Violations (Import Analysis)**
   ```javascript
   // auth.js
   exports.requireAuth = (req, res, next) => { ... }
   
   // patients.js
   const { requireAuth } = require('./auth');  // Imported but unused
   ```
   - **Aegis sees:** Import statement (syntactically valid)
   - **Bob sees:**
     - `requireAuth` is imported but never referenced in function calls
     - Other files in same directory use `requireAuth` consistently
     - **Conclusion:** Dead import suggests missing auth enforcement

### 3.3 Division of Labor (Summary Table)

| Capability | Aegis (Deterministic) | Bob (Contextual) |
|------------|----------------------|------------------|
| **Syntax violations** | ✅ Hardcoded credentials, weak crypto | ❌ |
| **Single-file patterns** | ✅ Session timeout, plaintext storage | ❌ |
| **Cross-file imports** | ❌ | ✅ Middleware chain analysis |
| **Data flow tracing** | ❌ | ✅ PHI from model → route → response |
| **Inconsistency detection** | ❌ | ✅ "Why does route A have auth but B doesn't?" |
| **Intent reasoning** | ❌ | ✅ "Developer imported requireAuth but forgot to use it" |
| **Remediation generation** | ❌ | ✅ Generate PR with fix + explanation |
| **Speed** | ⚡ Milliseconds per file | 🐢 Seconds per analysis |
| **False positives** | 📊 Low (pattern-based) | 📊 Medium (requires validation) |

**Design Principle:** Aegis does the heavy lifting (fast, exhaustive scanning). Bob does the nuanced reasoning (slow, context-aware analysis). Together, they provide comprehensive HIPAA compliance auditing.

---

## 4. File and Folder Structure

```
Aegis/
├── .aegis/                          # Runtime data (gitignored)
│   └── findings.db                  # SQLite database (CWD-relative)
│
├── Aegis/                           # Python package (lowercase in imports)
│   ├── __init__.py                  # Package root
│   ├── cli.py                       # Click CLI (scan, report, serve-mcp)
│   ├── database.py                  # SQLAlchemy models + session factory
│   ├── mcp_server.py                # MCP server entrypoint (stdio transport)
│   ├── models.py                    # Pydantic models (Finding, Evidence, CFRCitation, Report)
│   │
│   ├── api/                         # FastAPI backend for dashboard
│   │   ├── __init__.py
│   │   └── main.py                  # Endpoints: /findings, /reports, /scan
│   │
│   ├── reporter/                    # Report generation
│   │   ├── __init__.py
│   │   ├── json_export.py           # JSON serialization
│   │   └── pdf.py                   # ReportLab PDF generation
│   │
│   ├── rules/                       # HIPAA rule implementations
│   │   ├── __init__.py
│   │   ├── base.py                  # Rule ABC (check method contract)
│   │   ├── ac_1_access_control.py   # §164.312(a)(1) — Auth required
│   │   ├── ac_2_session_timeout.py  # §164.312(a)(2)(iii) — Session timeout
│   │   ├── ac_3_authentication.py   # §164.312(d) — Auth strength
│   │   ├── au_1_audit_logs.py       # §164.312(b) — Audit logging
│   │   ├── en_1_encryption.py       # §164.312(a)(2)(iv) — Encryption at rest
│   │   ├── tr_1_transmission.py     # §164.312(e)(1) — Transmission security
│   │   └── in_1_integrity.py        # §164.312(c)(1) — Integrity controls
│   │
│   └── scanner/                     # File discovery + parsing
│       ├── __init__.py
│       ├── base.py                  # Scanner ABC, SourceFile dataclass
│       ├── pattern_matcher.py       # Regex-based fallback (SQL, JSON)
│       └── tree_sitter.py           # Tree-sitter AST parser (JS/TS)
│
├── dashboard/                       # React frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── main.tsx                 # App entrypoint
│   │   ├── App.tsx                  # Root component (routing)
│   │   ├── index.css                # Tailwind imports
│   │   ├── components/
│   │   │   └── ui/                  # shadcn/ui components
│   │   │       ├── badge.tsx
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       ├── dialog.tsx
│   │   │       ├── table.tsx
│   │   │       └── tabs.tsx
│   │   ├── lib/
│   │   │   ├── api.ts               # Axios client for FastAPI
│   │   │   └── utils.ts             # Tailwind cn() helper
│   │   └── pages/
│   │       ├── Overview.tsx         # Severity distribution, recent scans
│   │       ├── Findings.tsx         # Filterable findings table
│   │       └── Reports.tsx          # Report history + download
│   ├── package.json                 # Node.js dependencies
│   ├── vite.config.ts               # Vite build config
│   ├── tsconfig.json                # TypeScript config
│   ├── tailwind.config.js           # Tailwind CSS config
│   └── Dockerfile                   # Production container image
│
├── demo/
│   └── patient-portal/              # Deliberately vulnerable Express.js app
│       ├── server.js                # Express app entrypoint
│       ├── seed.sql                 # PostgreSQL seed data
│       ├── package.json             # Node.js dependencies
│       ├── Dockerfile               # Container image
│       ├── config/
│       │   └── database.js          # Sequelize config (ssl: false)
│       ├── middleware/
│       │   └── session.js           # Session config (24h timeout)
│       ├── models/                  # Sequelize models
│       │   ├── Appointment.js
│       │   ├── AuditLog.js
│       │   ├── Medication.js
│       │   ├── Patient.js           # Plaintext SSN storage
│       │   └── User.js
│       └── routes/                  # Express route handlers
│           ├── admin.js
│           ├── appointments.js
│           ├── auth.js              # Hardcoded admin/admin
│           ├── medications.js
│           └── patients.js          # Missing auth on GET /:id
│
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md              # This file
│   ├── DEMO-SCRIPT.md               # Judging walkthrough
│   └── HIPAA-RULES.md               # Rule catalog with CFR citations
│
├── scripts/                         # Utility scripts
│   ├── setup.py                     # Install Python package + dashboard deps
│   ├── run_audit.py                 # End-to-end audit script
│   └── seed_demo.py                 # Seed demo database
│
├── tests/                           # Pytest test suite
│   ├── __init__.py
│   ├── test_cli.py                  # CLI command tests
│   └── test_models.py               # Pydantic model tests
│
├── .bob/                            # Bob hackathon session data
│   └── rules-*/                     # Mode-specific session logs
│
├── .env.example                     # Environment variable template
├── .gitignore                       # Git exclusions
├── AGENTS.md                        # Agent rules (build commands, patterns)
├── docker-compose.yml               # Demo stack (portal + dashboard + postgres)
├── LICENSE                          # MIT license
├── pyproject.toml                   # Python package metadata + dependencies
└── README.md                        # Project overview
```

### Key Structural Decisions

1. **Python Package Name:** `aegis` (lowercase) but directory is `Aegis/` (capitalized)
   - **Rationale:** Follows Python convention (package names lowercase, directory can be capitalized)
   - **Import:** `from aegis.models import Finding`

2. **Database Location:** `.aegis/findings.db` relative to **CWD**, not project root
   - **Rationale:** Allows scanning external projects without polluting their directories
   - **Caveat:** Users must run `aegis scan` from consistent directory

3. **Three Separate Node.js Projects:**
   - `dashboard/` — React frontend
   - `demo/patient-portal/` — Vulnerable demo app
   - Each has own `package.json`, `node_modules/`, build process
   - **Rationale:** Decouples frontend from demo; dashboard can be deployed independently

4. **Rules Naming Convention:** `{id}_{name}.py`
   - Example: `ac_1_access_control.py`, `en_1_encryption.py`
   - **Rationale:** Alphabetical sorting matches severity priority (AC → AU → EN → TR → IN)

5. **MCP Server as Separate Module:** `mcp_server.py` at package root
   - **Rationale:** MCP is an integration layer, not core business logic
   - **Future:** Could move to `aegis/integrations/mcp.py` if other integrations added

---

## 5. Key Design Decisions and Tradeoffs

### 5.1 Tree-Sitter vs. Regex

**Decision:** Use tree-sitter for JS/TS, regex for SQL/JSON

**Rationale:**
- **Tree-sitter pros:** Accurate AST parsing, handles complex syntax, language-agnostic
- **Tree-sitter cons:** Requires language grammar binaries, slower than regex
- **Regex pros:** Fast, no dependencies, good for simple patterns (SQL keywords)
- **Regex cons:** Fragile, can't handle nested structures

**Tradeoff:** Accuracy vs. speed. Tree-sitter for primary targets (JS/TS routes), regex for secondary targets (SQL migrations).

**Alternative Considered:** Babel parser for JS/TS
- **Rejected:** Babel is JS-specific; tree-sitter supports 40+ languages (future-proof)

### 5.2 SQLite vs. PostgreSQL

**Decision:** SQLite for findings database

**Rationale:**
- **SQLite pros:** Zero-config, single file, fast for read-heavy workloads
- **SQLite cons:** No concurrent writes, limited scalability
- **Use case:** Local dev tool, single-user, findings are append-only

**Tradeoff:** Simplicity vs. scalability. SQLite is sufficient for hackathon scope.

**Alternative Considered:** PostgreSQL
- **Rejected:** Overkill for local tool; adds deployment complexity

**Future:** If Aegis becomes multi-user SaaS, migrate to PostgreSQL with connection pooling.

### 5.3 MCP stdio vs. TCP

**Decision:** stdio transport for MCP server

**Rationale:**
- **stdio pros:** Simple IPC, no port conflicts, works with local Bob
- **stdio cons:** Single client, no remote access
- **Use case:** Bob runs on same machine as Aegis

**Tradeoff:** Simplicity vs. multi-client support. stdio is sufficient for local agent.

**Alternative Considered:** TCP transport on `--port`
- **Rejected for v0.1:** Adds auth complexity (who can connect?)
- **Future:** Implement TCP for remote Bob instances (e.g., cloud-hosted agents)

### 5.4 Per-File vs. Cross-File Rules

**Decision:** Aegis does per-file, Bob does cross-file

**Rationale:**
- **Per-file pros:** Fast, parallelizable, deterministic
- **Per-file cons:** Misses import relationships, data flow
- **Cross-file pros:** Comprehensive, context-aware
- **Cross-file cons:** Slow, requires LLM reasoning

**Tradeoff:** Speed vs. completeness. Aegis provides fast baseline, Bob adds depth.

**Alternative Considered:** Aegis does cross-file analysis with static analysis tools (e.g., ESLint, Semgrep)
- **Rejected:** Static analysis tools are rule-based, not context-aware. Bob's LLM reasoning is more flexible.

### 5.5 PDF vs. HTML Reports

**Decision:** PDF as primary report format

**Rationale:**
- **PDF pros:** Portable, printable, professional appearance
- **PDF cons:** Not interactive, harder to generate
- **Use case:** Compliance audits require archival-quality reports

**Tradeoff:** Portability vs. interactivity. PDF for compliance, JSON for CI/CD.

**Alternative Considered:** HTML reports
- **Rejected:** HTML requires hosting or local file:// URLs (security issues)
- **Future:** Add HTML export for web-based dashboards

### 5.6 Hardcoded CFR Citations vs. External Database

**Decision:** CFR text hardcoded in rule classes

**Rationale:**
- **Hardcoded pros:** No external dependencies, fast lookup
- **Hardcoded cons:** Manual updates if CFR changes
- **Use case:** CFR text is stable (last updated 2013)

**Tradeoff:** Maintainability vs. simplicity. Hardcoded is sufficient for stable regulations.

**Alternative Considered:** Fetch CFR text from HHS API
- **Rejected:** Adds network dependency, API rate limits
- **Future:** If CFR updates frequently, switch to external source

### 5.7 Dashboard CORS Restriction

**Decision:** Hardcode CORS to `http://localhost:5173`

**Rationale:**
- **Security:** Prevents unauthorized dashboard access
- **Simplicity:** No CORS config needed for local dev
- **Use case:** Dashboard is local dev tool

**Tradeoff:** Security vs. flexibility. Hardcoded is sufficient for single-user tool.

**Alternative Considered:** Allow all origins (`*`)
- **Rejected:** Security risk if FastAPI is exposed to network
- **Future:** Add `--cors-origin` CLI flag for custom origins

### 5.8 Line Number Indexing (1-based)

**Decision:** [`pattern_matcher.find_all()`](../Aegis/scanner/pattern_matcher.py:25) returns 1-based line numbers

**Rationale:**
- **1-based pros:** Matches editor line numbers, user-friendly
- **1-based cons:** Differs from Python's 0-based indexing
- **Use case:** Evidence model expects 1-based lines for display

**Tradeoff:** User-friendliness vs. internal consistency. 1-based matches user expectations.

**Alternative Considered:** 0-based indexing
- **Rejected:** Requires +1 conversion in every display context

---

## 6. Performance Characteristics

### 6.1 Scan Performance

**Benchmark:** Demo patient-portal (15 files, ~1,200 LOC)
- **Scanner.walk():** ~5ms (file discovery)
- **Scanner.parse():** ~50ms (tree-sitter parsing)
- **Rules.check():** ~100ms (7 rules × 15 files)
- **Database.insert():** ~10ms (12 findings)
- **Total:** ~165ms

**Scaling:** Linear with file count. 1,000 files ≈ 11 seconds.

**Bottleneck:** Tree-sitter parsing (50ms per file). Parallelizable with multiprocessing.

### 6.2 MCP Tool Latency

**Benchmark:** Local stdio transport
- `list_findings()`: ~5ms (SQLite query)
- `get_finding()`: ~2ms (primary key lookup)
- `explain_rule()`: ~1ms (in-memory lookup)
- `run_scan()`: ~165ms (full scan, see above)
- `generate_report()`: ~200ms (PDF rendering)

**Bottleneck:** PDF rendering (ReportLab). JSON export is ~10ms.

### 6.3 Dashboard Load Time

**Benchmark:** Vite dev server (localhost:5173)
- Initial load: ~500ms (React hydration)
- Findings table: ~50ms (fetch + render 100 rows)
- Evidence viewer: ~10ms (syntax highlighting)

**Bottleneck:** React hydration. Production build with code splitting would improve.

---

## 7. Security Considerations

### 7.1 Threat Model

**Assumptions:**
- Aegis runs on trusted developer machines
- Scanned codebases may contain malicious code
- Dashboard is local-only (no public exposure)

**Threats:**
1. **Malicious code execution during scan**
   - **Mitigation:** Aegis only parses code (AST), never executes it
2. **SQL injection in findings database**
   - **Mitigation:** SQLAlchemy ORM with parameterized queries
3. **XSS in dashboard evidence viewer**
   - **Mitigation:** React auto-escapes JSX; syntax highlighter is sandboxed
4. **Unauthorized MCP access**
   - **Mitigation:** stdio transport requires local process access

### 7.2 Data Privacy

**PHI Handling:**
- Aegis **does not** store PHI from scanned codebases
- Evidence snippets are **code**, not patient data
- Database contains only file paths, line numbers, and code snippets

**Example:** Finding for `GET /patients/:id` stores:
```json
{
  "file": "routes/patients.js",
  "line_start": 24,
  "snippet": "router.get('/:id', async (req, res) => { ... })",
  "why": "Route handler accesses PHI without authentication middleware"
}
```
**No PHI:** No patient names, SSNs, or medical records stored.

---

## 8. Future Enhancements

### 8.1 Planned Features (Post-Hackathon)

1. **Multi-Language Support**
   - Python (Flask/Django), Java (Spring Boot), C# (ASP.NET)
   - Tree-sitter grammars available for all

2. **CI/CD Integration**
   - GitHub Actions workflow: `aegis scan . --fail-on critical`
   - GitLab CI, Jenkins plugins

3. **Custom Rules**
   - User-defined rules in YAML: `custom_rules/my_rule.yaml`
   - Rule DSL for non-programmers

4. **Incremental Scanning**
   - Only scan changed files (git diff integration)
   - Cache AST trees for unchanged files

5. **Bob Remediation Workflow**
   - Auto-generate PRs with fixes
   - Interactive remediation wizard in dashboard

6. **HIPAA Compliance Score**
   - Aggregate metric: "87% compliant (13 violations remaining)"
   - Trend tracking over time

### 8.2 Known Limitations

1. **No Runtime Analysis**
   - Aegis is static analysis only
   - Cannot detect runtime-only violations (e.g., SQL injection via user input)

2. **False Negatives**
   - Dynamic middleware registration not detected
   - Obfuscated code may bypass pattern matching

3. **False Positives**
   - Test files may trigger violations (e.g., hardcoded test credentials)
   - Mitigation: Add `.aegisignore` file (like `.gitignore`)

4. **Single-Repo Scope**
   - Cannot analyze microservices across multiple repos
   - Mitigation: Bob can aggregate findings from multiple scans

---

## 9. References

### 9.1 Standards and Regulations

- **HIPAA Security Rule:** 45 CFR Part 164, Subpart C
  - https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164
- **HHS Security Rule Summary:** https://www.hhs.gov/hipaa/for-professionals/security/
- **NIST SP 800-66r2:** HIPAA Security Rule Implementation Guide

### 9.2 Technologies

- **Tree-sitter:** https://tree-sitter.github.io/tree-sitter/
- **Model Context Protocol (MCP):** https://modelcontextprotocol.io/
- **ReportLab:** https://www.reportlab.com/docs/reportlab-userguide.pdf
- **FastAPI:** https://fastapi.tiangolo.com/
- **React + Vite:** https://vitejs.dev/guide/
- **shadcn/ui:** https://ui.shadcn.com/

### 9.3 Related Work

- **Semgrep:** Static analysis tool with HIPAA rules (commercial)
- **Snyk Code:** Security scanner with compliance checks (commercial)
- **SonarQube:** Code quality + security (limited HIPAA support)

**Aegis Differentiator:** Open-source, HIPAA-specific, Bob integration for contextual reasoning.

---

## Appendix A: Glossary

- **AST:** Abstract Syntax Tree — hierarchical representation of source code structure
- **CFR:** Code of Federal Regulations — U.S. legal code
- **MCP:** Model Context Protocol — standard for LLM tool integration
- **PHI:** Protected Health Information — patient data covered by HIPAA
- **Tree-sitter:** Incremental parsing library for syntax trees

## Appendix B: Contact

For questions about this architecture, contact the Aegis team:
- **GitHub:** [Aegis Repository](https://github.com/your-org/aegis)
- **Email:** aegis-dev@example.com

---

**Document Version:** 1.0  
**Last Reviewed:** 2026-05-15  
**Next Review:** Post-hackathon (2026-06-01)