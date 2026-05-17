# Aegis Demo Script

## 1. COLD OPEN

In my second year of university, I helped build an NLP system for a healthcare startup with thirteen clinics across two Ottawa hospitals. The product was ready. The users were waiting. They couldn't ship for nine months — because of compliance review.

(~30 seconds)

## 2. PROBLEM

HIPAA compliance review is a months-long manual process. Mid-size healthcare companies spend over five hundred thousand dollars per year on audit firms to manually review code for Technical Safeguards violations. Healthcare software gets blocked behind compliance teams who read through thousands of lines of code looking for authentication gaps, encryption failures, and audit log omissions. Add SOC 2 and FedRAMP requirements, and you're looking at years of delay before a single line of production code ships.

(~30 seconds)

## 3. SOLUTION

Aegis is a HIPAA Technical Safeguards compliance auditor that scans code for violations of 45 CFR section 164.312 and produces audit-ready findings with CFR citations and evidence. Bob, running in a custom Auditor mode, autonomously generates remediation pull requests with regulatory citations. The critical innovation: Bob built the MCP rules engine that Bob then uses to audit code. This is recursive engineering — an AI agent building the compliance infrastructure it operates within.

(~30 seconds)

## 4. LIVE DEMO

[SCREEN: terminal showing scan command running]

We run Aegis against a deliberately vulnerable patient portal. The scan completes in under two hundred milliseconds and identifies seventeen findings with a risk score of zero out of one hundred — meaning critical violations exist.

(~20 seconds)

[SCREEN: audit PDF on screen, scroll to one Critical finding]

The PDF report shows a Critical finding: unauthenticated access to protected health information on the GET patients endpoint. The finding includes the exact CFR citation — 45 CFR section 164.312(a)(1) — the file path, line number, code snippet, and remediation guidance. This is audit-ready documentation that compliance teams can submit directly to regulators.

(~30 seconds)

[SCREEN: Bob IDE in Auditor mode showing cross-file analysis]

Here's where Bob's cross-file reasoning becomes critical. The error handler in server.js logs error messages from failed Patient queries. Bob traces the data flow: the Patient model defines an SSN field, routes/patients.js queries Patient.findByPk, when that query fails the error object contains patient data, and server.js logs that error to the application logs. This is a PHI leak that spans three files. Per-file scanning cannot catch this — you need contextual reasoning across module boundaries to understand that patient data is flowing into log statements.

(~30 seconds)

[SCREEN: GitHub PR pull/2]

Bob generated a remediation pull request with three commits. Commit one adds authentication middleware to the patients endpoint with a CFR comment. Commit two removes hardcoded credentials. Commit three adds field-level encryption for SSN storage. Each commit includes a new test file verifying the fix. The PR description cites the Report ID, includes before and after code snippets, and references the specific CFR sections. This PR is open and unmerged — it's ready for human review.

(~30 seconds)

[SCREEN: terminal showing post-fix scan]

After applying the fixes, we run a fresh scan. Fourteen findings remain — down from seventeen. The three highest-risk vectors are closed: unauthenticated PHI access, hardcoded credentials, and plaintext SSN assignment in the POST handler.

(~15 seconds)

[SCREEN: bob_sessions folder in file explorer]

The bob_sessions directory contains eight session logs documenting every step of Aegis development. Session two shows Bob designing the architecture in Plan mode. Session four shows Bob implementing the MCP server in Code mode. Session six shows the cross-file PHI flow analysis in Auditor mode. This is the complete audit trail of Bob's work — architecture decisions, implementation reasoning, and compliance analysis.

(~15 seconds)

## 5. ARCHITECTURE BEAT

The architecture separates deterministic scanning from contextual reasoning. The MCP rules engine exposes seven encoded HIPAA rules through five tools: list findings, get finding, explain rule, run scan, and generate report. The tree-sitter AST scanner performs surgical per-file detection. Bob, running in the custom Auditor mode, coordinates multi-component workflows: triggering scans via MCP, analyzing cross-file violations, generating remediation PRs, and producing executive summaries. The Orchestrator pattern lets Bob delegate subtasks to appropriate modes while maintaining state across the pipeline.

(~20 seconds)

## 6. ROADMAP CLOSE

HIPAA Technical Safeguards are live today. SOC 2 controls ship in two weeks. GDPR Article 32 technical measures in four weeks. FedRAMP moderate baseline in eight weeks. Multi-tenant SaaS with team collaboration in three months. Compliance that ships with your code.

(~30 seconds)

---

**Total target duration:** 3 minutes 25 seconds
