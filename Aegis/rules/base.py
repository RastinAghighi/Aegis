"""Rule ABC. Each rule scans a SourceFile (or iterable thereof) and yields Findings."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable

from ..models import CFRCitation, Evidence, Finding, Severity


class RuleBase(ABC):
    """A single HIPAA control check.
    
    Subclasses must define:
    - rule_id: str (e.g., "AC-1")
    - cfr: str (e.g., "164.312(a)(1)")
    - title: str
    - description: str
    - severity: Severity
    - remediation_template: str
    
    And implement:
    - match_js(tree, file_path, context) -> list[Finding]
    """

    rule_id: str
    cfr: str
    title: str
    description: str
    severity: Severity
    remediation_template: str

    @staticmethod
    def normalize_path(file_path: str) -> str:
        # Always compare paths with forward slashes so checks like "/routes/" in path
        # work on Windows (where Path stringifies with backslashes).
        return file_path.replace("\\", "/").lower()

    def create_finding(
        self,
        file_path: str,
        line_start: int,
        line_end: int,
        snippet: str,
        why: str,
    ) -> Finding:
        """Helper to create a Finding with this rule's metadata."""
        return Finding(
            rule_id=self.rule_id,
            rule_title=self.title,
            severity=self.severity,
            cfr=CFRCitation(
                section=self.cfr,
                title=self.title,
                text=self.description,
                url=f"https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-{self.cfr.replace('(', '-').replace(')', '')}",
            ),
            evidence=Evidence(
                file=file_path,
                line_start=line_start,
                line_end=line_end,
                snippet=snippet,
                why=why,
            ),
            remediation=self.remediation_template,
        )

    @abstractmethod
    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Finding]:
        """Scan a JavaScript/TypeScript file and return findings.
        
        Args:
            tree: tree-sitter AST root node
            file_path: Path to the file being scanned
            context: Additional context (e.g., file content, other files in repo)
            
        Returns:
            List of Finding objects for violations detected
        """
        raise NotImplementedError


__all__ = ["RuleBase", "Severity", "CFRCitation"]

# Made with Bob
