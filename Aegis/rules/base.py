"""Rule ABC. Each rule scans a SourceFile (or iterable thereof) and yields Findings."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from ..models import CFRCitation, Finding, Severity
from ..scanner.base import SourceFile


class Rule(ABC):
    """A single HIPAA control check."""

    # ----- subclass contract -----
    id: str  # e.g. "AC-1"
    title: str  # e.g. "Access Control — auth required"
    severity: Severity
    cfr: CFRCitation
    remediation: str

    @abstractmethod
    def check(self, sources: Iterable[SourceFile]) -> Iterable[Finding]:
        """Yield Findings for any violations detected across `sources`."""
        raise NotImplementedError


__all__ = ["Rule", "Severity", "CFRCitation"]
