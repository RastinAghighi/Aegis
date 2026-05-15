"""Smoke tests for the Pydantic models."""

from aegis.models import CFRCitation, Evidence, Finding, Report, Severity


def _finding(rule: str = "AC-1", sev: Severity = Severity.CRITICAL) -> Finding:
    return Finding(
        rule_id=rule,
        rule_title="Access Control",
        severity=sev,
        cfr=CFRCitation(
            section="164.312(a)(1)",
            title="Access control",
            text="Implement technical policies and procedures...",
        ),
        evidence=Evidence(
            file="demo/x.js",
            line_start=10,
            line_end=12,
            snippet="app.get('/patients/:id', ...)",
            why="route has no auth middleware",
        ),
        remediation="Bind requireAuth middleware before the handler.",
    )


def test_report_counts() -> None:
    r = Report(target="demo/patient-portal")
    r.findings.append(_finding(sev=Severity.CRITICAL))
    r.findings.append(_finding(sev=Severity.HIGH))
    r.findings.append(_finding(sev=Severity.HIGH))
    assert r.counts_by_severity == {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 0, "LOW": 0}


def test_finding_round_trip() -> None:
    f = _finding()
    blob = f.model_dump(mode="json")
    f2 = Finding.model_validate(blob)
    assert f2.rule_id == "AC-1"
    assert f2.severity is Severity.CRITICAL
