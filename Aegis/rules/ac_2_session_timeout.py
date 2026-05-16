"""AC-2: Automatic Logoff - Detect session timeouts exceeding 30 minutes.

45 CFR § 164.312(a)(2)(iii) - Automatic logoff
"""

from __future__ import annotations

from typing import Any

from ..models import Severity
from .base import RuleBase


class AC2SessionTimeout(RuleBase):
    """Detect session configurations with excessive timeout periods."""

    rule_id = "AC-2"
    cfr = "164.312(a)(2)(iii)"
    title = "Automatic Logoff"
    description = (
        "Implement electronic procedures that terminate an electronic session "
        "after a predetermined time of inactivity."
    )
    severity = Severity.HIGH
    remediation_template = (
        "Set session maxAge to 30 minutes (1800000 ms) or less. "
        "Example: session({ cookie: { maxAge: 1800000 } })"
    )

    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Any]:
        """Scan JavaScript file for excessive session timeouts."""
        # TODO: Implement detection of session({ cookie: { maxAge: X } }) where X > 1800000
        # Use find_object_literals to find session config objects
        # Check maxAge values and flag if > 30 minutes
        # NOTE: For any file_path string matching, use self.normalize_path(file_path)
        # so Windows backslash paths still match patterns like "/config/".
        return []


# Singleton instance for easy import
ac2_rule = AC2SessionTimeout()

__all__ = ["AC2SessionTimeout", "ac2_rule"]

# Made with Bob
