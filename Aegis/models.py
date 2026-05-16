"""Pydantic models for findings, evidence, and reports."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class CFRCitation(BaseModel):
    """A 45 CFR §164 citation attached to a finding."""

    section: str = Field(..., description="e.g. '164.312(a)(1)'")
    title: str = Field(..., description="Short title, e.g. 'Access control'")
    text: str = Field(..., description="Verbatim CFR paragraph text")
    url: str | None = Field(
        default=None, description="Link to eCFR or HHS reference"
    )


class Evidence(BaseModel):
    """Where and why the violation was detected."""

    file: str
    line_start: int
    line_end: int
    snippet: str
    why: str = Field(..., description="One-sentence explanation of the match")


class Finding(BaseModel):
    """A single rule violation."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    rule_id: str = Field(..., description="e.g. 'AC-1', 'EN-1'")
    rule_title: str
    severity: Severity
    cfr: CFRCitation
    evidence: Evidence
    remediation: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Report(BaseModel):
    """A scan report — collection of findings plus summary metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    target: str = Field(..., description="Absolute or repo-relative path scanned")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    findings: list[Finding] = Field(default_factory=list)

    @property
    def counts_by_severity(self) -> dict[str, int]:
        out: dict[str, int] = {s.value: 0 for s in Severity}
        for f in self.findings:
            out[f.severity.value] += 1
        return out

    @property
    def risk_score(self) -> int:
        """Calculate risk score: max(0, 100 - (10*critical + 5*high + 2*medium + 1*low))"""
        counts = self.counts_by_severity
        score = 100 - (
            10 * counts["CRITICAL"]
            + 5 * counts["HIGH"]
            + 2 * counts["MEDIUM"]
            + 1 * counts["LOW"]
        )
        return max(0, score)
