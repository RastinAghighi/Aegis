"""EN-1 — Encryption at Rest. 45 CFR §164.312(a)(2)(iv).

TODO (Bob): flag PHI columns (ssn, dob, mrn, diagnosis) without encryption wrapper,
and plaintext assignments like `patient.ssn = req.body.ssn`.
"""
