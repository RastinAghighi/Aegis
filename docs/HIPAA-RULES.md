# HIPAA Rule Catalog

This is the canonical reference for the rules Aegis enforces. Each rule maps to
one or more sections of the HIPAA Security Rule (45 CFR Part 164, Subpart C).
The CFR citation strings below are the exact text Aegis emits in evidence.

> **Scope note.** Aegis focuses on the Security Rule's *Technical Safeguards*
> (§164.312). Administrative and physical safeguards (§164.308, §164.310) are
> out of scope for static code analysis.

---

## AC-1 — Access Control (authentication required for PHI endpoints)

- **CFR:** 45 CFR §164.312(a)(1) — *Access control. Implement technical
  policies and procedures for electronic information systems that maintain
  electronic protected health information to allow access only to those
  persons or software programs that have been granted access rights.*
- **Detects:** route handlers that read/write PHI without an authentication
  middleware in the resolved middleware chain.
- **Severity:** CRITICAL
- **Example violation:** `app.get('/patients/:id', (req, res) => {...})` with no
  `requireAuth`/`authenticate`/`passport` middleware bound.

## AC-2 — Session Timeout

- **CFR:** 45 CFR §164.312(a)(2)(iii) — *Automatic logoff. Implement
  electronic procedures that terminate an electronic session after a
  predetermined time of inactivity.*
- **Detects:** session cookie `maxAge`/`expires`/`ttl` exceeding 15 minutes
  (900,000 ms) or absent.
- **Severity:** HIGH
- **Example violation:** `session({ cookie: { maxAge: 86400000 } })` — 24h.

## AC-3 — Authentication Strength

- **CFR:** 45 CFR §164.312(d) — *Person or entity authentication. Implement
  procedures to verify that a person or entity seeking access to electronic
  protected health information is the one claimed.*
- **Detects:** hardcoded credentials, default passwords, plaintext comparison
  against literals, missing password hashing (`bcrypt`/`argon2`/`scrypt`).
- **Severity:** CRITICAL
- **Example violation:**
  `if (username === 'admin' && password === 'admin') { ... }`

## AU-1 — Audit Logging

- **CFR:** 45 CFR §164.312(b) — *Audit controls. Implement hardware, software,
  and/or procedural mechanisms that record and examine activity in information
  systems that contain or use electronic protected health information.*
- **Detects:** PHI read/write code paths (anything touching Patient, Medication,
  Appointment models) that do not call into an audit-log sink.
- **Severity:** HIGH
- **Example violation:** `Patient.findByPk(id)` returned to client with no
  `AuditLog.create(...)` call on the same path.

## EN-1 — Encryption at Rest

- **CFR:** 45 CFR §164.312(a)(2)(iv) — *Encryption and decryption. Implement
  a mechanism to encrypt and decrypt electronic protected health information.*
- **Detects:** PHI fields (SSN, DOB, MRN, diagnosis) stored as plaintext
  `STRING`/`TEXT` columns with no encryption wrapper, or assignments such as
  `patient.ssn = req.body.ssn` with no `encrypt(...)` call.
- **Severity:** CRITICAL
- **Example violation:** `ssn: { type: DataTypes.STRING }` in a Sequelize model.

## TR-1 — Transmission Security

- **CFR:** 45 CFR §164.312(e)(1) — *Transmission security. Implement technical
  security measures to guard against unauthorized access to electronic
  protected health information that is being transmitted over an electronic
  communications network.*
- **Detects:** `ssl: false` in database configs, HTTP (not HTTPS) URLs in
  outbound API calls, missing `helmet`/`hsts` middleware.
- **Severity:** HIGH
- **Example violation:** `axios.get('http://internal-pharmacy-api/...')`.

## IN-1 — Integrity Controls

- **CFR:** 45 CFR §164.312(c)(1) — *Integrity. Implement policies and
  procedures to protect electronic protected health information from improper
  alteration or destruction.*
- **Detects:** mass-update statements (`Model.update(..., { where: ... })`
  without scoped `id`/`uuid` predicate), missing optimistic locking
  (`version` column or `If-Match` header), bulk delete with no integrity
  check.
- **Severity:** HIGH
- **Example violation:**
  `Medication.update({ status }, { where: { patient_id } })`

---

## Evidence model

Each finding emitted by Aegis carries:

- `rule_id` — one of `AC-1`, `AC-2`, `AC-3`, `AU-1`, `EN-1`, `TR-1`, `IN-1`
- `cfr` — citation string above (incl. section + paragraph + verbatim text)
- `severity` — `CRITICAL` | `HIGH` | `MEDIUM` | `LOW`
- `evidence` — `{ file, line_start, line_end, snippet, why }`
- `remediation` — short suggested fix

See `aegis/models.py` for the Pydantic schema.

## References

- HHS Security Rule summary: https://www.hhs.gov/hipaa/for-professionals/security/
- 45 CFR Part 164 (eCFR): https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164
- NIST SP 800-66r2 (HIPAA Security Rule implementation guide)
