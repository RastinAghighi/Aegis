# Aegis

**HIPAA compliance auditor for code.**

*Compliance that ships with your code.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Built with IBM Bob](https://img.shields.io/badge/Built%20with-IBM%20Bob-blue.svg)](https://research.ibm.com/)

Live demo: [URL coming soon]
Demo video: [link coming soon]

---

## Why this exists

In my second year of university, I helped build an NLP system for a healthcare startup with thirteen clinics across two Ottawa hospitals. The product was ready. The users were waiting. They couldn't ship for nine months — because of compliance review.

HIPAA compliance review is months-long, manual, and expensive. Auditors read code line by line, trace data flows across files, and write evidence reports by hand. The cost falls hardest on small healthcare software teams who cannot afford a six-figure compliance engagement, so they either ship insecure software or do not ship at all. Aegis collapses that loop: deterministic scanners locate the patterns, an LLM auditor reasons across files, and the output is an evidence-cited report a Security Officer can sign.

---

## What it does

- **Detects HIPAA Security Rule violations in source code** using deterministic, per-file static analysis built on tree-sitter ASTs. Every finding carries a verbatim 45 CFR §164.312 citation, file/line evidence, and a remediation suggestion.
- **Reasons across files via MCP.** Aegis exposes findings to IBM Bob through the Model Context Protocol so Bob can trace PHI data flows across module boundaries — the kind of second-order violation per-file scanners cannot catch (e.g., a Patient model field that leaks through an error handler in a different file).
- **Produces audit-ready evidence.** PDF and JSON exports include CFR citations, evidence snippets, risk categorization, and a remediation pull request workflow that closes the loop from detection to fix.

---

## Architecture

```
┌──────────┐   ┌──────────────┐   ┌────────────┐   ┌──────────────────┐
│ Scanner  │──▶│ Rules Engine │──▶│ MCP Server │──▶│ Bob (Auditor)    │
│ tree-    │   │ AC-1..IN-1   │   │ stdio +    │   │ cross-file PHI   │
│ sitter   │   │ CFR citations│   │ JSON-RPC   │   │ flow analysis    │
└──────────┘   └──────────────┘   └────────────┘   └────────┬─────────┘
                                                            │
                                                            ▼
                                              ┌──────────────────────────┐
                                              │ Findings ─▶ Remediation  │
                                              │ PDF / JSON  PR (3 commits│
                                              │             + Jest tests)│
                                              └──────────────────────────┘
```

**Stack:** Python 3.11, FastAPI, React + Vite + TypeScript + Tailwind + shadcn/ui, tree-sitter, MCP (stdio transport), ReportLab.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full details, including the scanner/rules separation, the stdio transport decision, and the Pydantic evidence model.

---

## HIPAA Rules Covered

| ID    | Name                                | CFR Section            | Severity |
|-------|-------------------------------------|------------------------|----------|
| AC-1  | Access Control                      | 45 CFR §164.312(a)(1)  | CRITICAL |
| AC-2  | Session Timeout                     | 45 CFR §164.312(a)(2)(iii) | HIGH |
| AC-3  | Authentication Strength             | 45 CFR §164.312(d)     | CRITICAL |
| AU-1  | Audit Logging                       | 45 CFR §164.312(b)     | HIGH     |
| EN-1  | Encryption at Rest                  | 45 CFR §164.312(a)(2)(iv) | CRITICAL |
| IN-1  | Integrity Controls                  | 45 CFR §164.312(c)(1)  | HIGH     |
| TR-1  | Transmission Security               | 45 CFR §164.312(e)(1)  | HIGH     |

Full rule catalog with detection patterns and verbatim CFR text: [docs/HIPAA-RULES.md](docs/HIPAA-RULES.md).

---

## How IBM Bob is used

Aegis was built entirely using IBM Bob across eight documented sessions, demonstrating Bob's capability to architect, implement, audit, and remediate a production-grade HIPAA compliance tool. The project showcases recursive engineering: Bob built the MCP rules engine that Bob then uses to audit code.

**Architecture Design (Session #2, Plan Mode):** Bob designed the complete system architecture in Plan mode, producing the 915-line ARCHITECTURE.md that defines the scanner/rules/MCP separation. The architecture document specifies the critical design decision that Aegis performs deterministic per-file scanning while Bob handles cross-file contextual analysis via MCP. Bob identified the tree-sitter vs. regex tradeoff, the stdio transport decision for MCP, and the 1-based line numbering convention that pattern_matcher.find_all() returns—details that became critical implementation constraints.

**Custom Mode Definition (Session #3, Plan Mode):** Bob defined the Auditor custom mode with a formal compliance persona: "senior HIPAA compliance auditor with 15 years of experience." The mode restricts tool access to MCP, file operations, and terminal execution—no browser tools. The persona enforces citation-heavy language where every violation claim must cite 45 CFR § 164.312 subsections. This mode configuration lives in `.bob/rules-auditor/` as project-specific rules, demonstrating Bob's ability to create domain-specific operational modes.

**MCP Rules Engine Implementation (Session #4, Code Mode):** Bob implemented the complete MCP server in mcp_server.py, exposing six tools: `list_rules`, `scan_file`, `scan_repo`, `get_rule`, `get_remediation_template`, and `generate_evidence`. The server uses stdio transport (JSON-RPC over stdin/stdout) rather than TCP, a design decision Bob documented in ARCHITECTURE.md section 5.3. Bob also implemented all seven HIPAA rules (AC-1, AC-2, AC-3, AU-1, EN-1, TR-1, IN-1) as Rule subclasses with check() methods that yield Finding objects containing Evidence and CFRCitation models. Each rule file includes verbatim CFR text hardcoded in the class definition—Bob's solution to avoid external API dependencies for stable regulatory text.

**First Compliance Audit (Session #5, Auditor Mode):** Bob executed the first audit in Auditor mode, calling the MCP server's run_scan() tool against demo/patient-portal. The audit identified 17 violations (15 CRITICAL, 2 HIGH) with formal CFR citations. Bob's analysis identified the top three risk categories: AC-1 unauthenticated PHI access triggering breach notification under § 164.404(a)(1), AC-3 hardcoded credentials bypassing § 164.312(d) authentication requirements, and EN-1 plaintext SSN storage violating the addressable encryption standard under § 164.312(a)(2)(iv). The audit output includes operational impact narratives: "The absence of authentication mechanisms creates an attack surface permitting unauthorized disclosure of PHI to any network-accessible actor."

**Cross-File PHI Flow Analysis (Session #6, Auditor Mode):** Bob performed cross-file analysis that per-file scanning cannot detect. The critical finding: server.js error handler logs PHI from failed Patient.findByPk() queries. Bob traced the data flow: Patient model defines SSN field → routes/patients.js queries Patient.findByPk() → query fails with patient object in error context → server.js error handler logs error.message containing patient data → PHI leaks to application logs. This multi-file reasoning demonstrates Bob's advantage over AST-based tools: Bob reads full repository context, understands import relationships, and traces data flow across module boundaries. The finding cites § 164.312(b) audit control requirements and § 164.308(a)(1)(ii)(D) information system activity review.

**Multi-File Remediation PR (Session #7, Auditor Mode):** Bob generated a three-commit remediation PR on branch aegis-remediation-critical. Commit 1: Added requireAuth middleware to GET /patients/:id with CFR comment "// 45 CFR § 164.312(a)(1) - Access Control". Commit 2: Removed hardcoded admin/admin credentials, replacing with bcrypt hash comparison. Commit 3: Added field-level encryption for SSN assignment in POST /patients handler. Each commit includes a new Jest test file (ac1-access-control.test.js, ac3-authentication.test.js, en1-encryption.test.js) verifying the fix. The PR description at REMEDIATION-PR.md includes before/after code snippets, references Report ID 5728bf4a-1dee-4654-ae70-f80239e9f734, and confirms post-remediation scan shows 14 remaining findings (down from 17). Bob executed the full workflow: branch creation, three sequential commits, test implementation, verification scan, and formal PR documentation.

**Orchestrator Pipeline (Session #8, Orchestrator Mode):** Bob coordinated a five-step audit pipeline across multiple modes. Step 1 (Advanced): MCP scan via run_scan() tool, verified 17 findings. Step 2 (Advanced): PDF report generation via generate_report() tool, produced 16-page audit-report-2.pdf with CFR citations and evidence snippets. Step 3 (Code): CLI scan execution via `py -m Aegis.cli scan demo/patient-portal --output findings.json`. Step 4 (Advanced): Executive summary generation, produced EXECUTIVE-SUMMARY.md with regulatory exposure analysis. Step 5 (Code): Verification that findings.json matches MCP scan results. This demonstrates Bob's orchestration capability: delegating subtasks to appropriate modes, maintaining state across mode switches, and coordinating multi-component operations.

**Audit Trail (bob_sessions/ Directory):** All eight sessions are exported to bob_sessions/ with full task descriptions, tool invocations, and results. Session files show Bob's reasoning: Session #2 includes the architectural tradeoff analysis (tree-sitter vs. Babel, SQLite vs. PostgreSQL, stdio vs. TCP). Session #4 shows Bob discovering the 1-based line numbering requirement and documenting it in AGENTS.md. Session #6 contains the cross-file PHI flow analysis with quoted code excerpts from server.js, routes/patients.js, and models/Patient.js. These exports provide judges complete visibility into Bob's decision-making process, tool usage patterns, and iterative problem-solving across 8 sessions spanning architecture, implementation, auditing, and remediation.

---

## Demo Target

`demo/patient-portal/` is an Express.js + PostgreSQL Patient Portal API deliberately seeded with **11 HIPAA violations** spanning access control, authentication, audit logging, encryption at rest, transmission security, and integrity. It is the fixture the scanner is exercised against and the codebase Bob audits in the demo walkthrough. Violations include unauthenticated `GET /patients/:id`, hardcoded `admin/admin` credentials in `routes/auth.js`, plaintext SSN columns in `models/Patient.js`, and an unscoped `Medication.update()` mass-update — each chosen to exercise a distinct rule and to surface at least one cross-file finding that only Bob can resolve.

---

## How to Run

### Local

**Windows (PowerShell):**

```powershell
git clone https://github.com/RastinAghighi/aegis.git
cd aegis
py -m pip install -e .
cd dashboard; npm install; cd ..
docker compose up
```

**macOS / Linux:**

```bash
git clone https://github.com/RastinAghighi/aegis.git
cd aegis
python -m pip install -e .
cd dashboard && npm install && cd ..
docker compose up
```

Once the stack is up:

```bash
aegis scan demo/patient-portal              # run the scanner
aegis report --format pdf --out report.pdf  # export PDF
aegis serve-mcp                             # launch MCP server for Bob
```

### Hosted

Or visit the live demo: [URL coming soon]

---

## Roadmap

| Capability                                | Timeline     |
|-------------------------------------------|--------------|
| HIPAA Technical Safeguards (§164.312)     | Live today   |
| SOC 2 Common Criteria                     | 2 weeks      |
| GDPR Article 32                           | 4 weeks      |
| FedRAMP Moderate baseline                 | 8 weeks      |
| Multi-tenant SaaS                         | 3 months     |

---

## About

**Rastin Aghighi** — Computer Science (AI minor), Queen's University, expected 2028.

- Email: rastinaghighi@gmail.com
- GitHub: [github.com/RastinAghighi](https://github.com/RastinAghighi)

---

## Acknowledgments

Built for the IBM Bob Hackathon, May 15–17 2026. The eight Bob session logs in `bob_sessions/` provide the complete audit trail of how Aegis was developed.

## License

MIT. See [LICENSE](LICENSE).
