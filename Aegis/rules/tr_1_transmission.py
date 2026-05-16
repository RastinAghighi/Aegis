"""TR-1: Transmission Security - Detect insecure data transmission.

45 CFR § 164.312(e)(1) - Transmission security
"""

from __future__ import annotations

from typing import Any

from ..models import Severity
from .base import RuleBase


class TR1Transmission(RuleBase):
    """Detect insecure transmission of PHI (unencrypted connections)."""

    rule_id = "TR-1"
    cfr = "164.312(e)(1)"
    title = "Transmission Security"
    description = (
        "Implement technical security measures to guard against unauthorized access "
        "to electronic protected health information that is being transmitted over "
        "an electronic communications network."
    )
    severity = Severity.CRITICAL
    remediation_template = (
        "1. Enable SSL/TLS for database connections: set dialectOptions.ssl to true or 'require'\n"
        "2. Use HTTPS URLs for all external API calls (https:// not http://)\n"
        "3. Ensure all PHI transmission uses encrypted channels."
    )

    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Any]:
        """Scan for insecure transmission configurations."""
        # TODO: Implement detection of:
        # 1. ssl: false in database config (find_object_literals with key 'ssl')
        # 2. http:// URLs in axios/fetch calls (search for string literals starting with 'http://')
        # Use find_object_literals and string literal searches
        # NOTE: For any file_path string matching, use self.normalize_path(file_path)
        # so Windows backslash paths still match patterns like "/config/".
        return []


# Singleton instance for easy import
tr1_rule = TR1Transmission()

__all__ = ["TR1Transmission", "tr1_rule"]

# Made with Bob
