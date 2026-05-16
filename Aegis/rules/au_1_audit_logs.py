"""AU-1: Audit Controls - Detect missing audit logging.

45 CFR § 164.312(b) - Audit controls
"""

from __future__ import annotations

from typing import Any

from ..models import Severity
from .base import RuleBase


class AU1AuditLogs(RuleBase):
    """Detect audit log models defined but not used."""

    rule_id = "AU-1"
    cfr = "164.312(b)"
    title = "Audit Controls"
    description = (
        "Implement hardware, software, and/or procedural mechanisms that record "
        "and examine activity in information systems that contain or use electronic "
        "protected health information."
    )
    severity = Severity.CRITICAL
    remediation_template = (
        "Implement audit logging for all PHI access. If AuditLog model exists, "
        "ensure AuditLog.create() is called for all sensitive operations. "
        "Log: actor, action, resource type, resource ID, timestamp, and IP address."
    )

    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Any]:
        """Scan for missing audit log usage."""
        # TODO: Implement project-wide check:
        # 1. Find if AuditLog model is defined (grep for 'AuditLog' in models/)
        # 2. Search all route files for AuditLog.create() calls
        # 3. Flag if model exists but no create() calls found
        # This requires cross-file analysis using context['all_files']
        # NOTE: For any file_path string matching (e.g., "/models/", "/routes/"), use
        # self.normalize_path(file_path) so Windows backslash paths still match.
        return []


# Singleton instance for easy import
au1_rule = AU1AuditLogs()

__all__ = ["AU1AuditLogs", "au1_rule"]

# Made with Bob
