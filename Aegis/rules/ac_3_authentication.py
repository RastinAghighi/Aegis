"""AC-3: Person/Entity Authentication - Detect hardcoded credentials.

45 CFR § 164.312(d) - Person or entity authentication
"""

from __future__ import annotations

from typing import Any

from ..models import Severity
from .base import RuleBase


class AC3Authentication(RuleBase):
    """Detect hardcoded credentials and weak authentication patterns."""

    rule_id = "AC-3"
    cfr = "164.312(d)"
    title = "Person or Entity Authentication"
    description = (
        "Implement procedures to verify that a person or entity seeking access "
        "to electronic protected health information is the one claimed."
    )
    severity = Severity.CRITICAL
    remediation_template = (
        "Remove hardcoded credentials. Use environment variables or secure credential "
        "management systems. Implement proper authentication with password hashing "
        "(e.g., bcrypt) and secure credential storage."
    )

    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Any]:
        """Scan JavaScript file for hardcoded credentials."""
        # TODO: Implement detection of patterns like:
        # - username === 'admin' && password === 'admin'
        # - password === 'hardcoded_value'
        # Use find_binary_expressions to find comparison chains
        # Flag any literal string comparisons for username/password
        # NOTE: For any file_path string matching, use self.normalize_path(file_path)
        # so Windows backslash paths still match patterns like "/routes/".
        return []


# Singleton instance for easy import
ac3_rule = AC3Authentication()

__all__ = ["AC3Authentication", "ac3_rule"]

# Made with Bob
