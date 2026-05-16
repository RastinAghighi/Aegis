"""IN-1: Integrity - Detect unsafe database update operations.

45 CFR § 164.312(c)(1) - Integrity
"""

from __future__ import annotations

from typing import Any

from ..models import Severity
from .base import RuleBase


class IN1Integrity(RuleBase):
    """Detect Sequelize Model.update() without proper where clauses."""

    rule_id = "IN-1"
    cfr = "164.312(c)(1)"
    title = "Integrity"
    description = (
        "Implement policies and procedures to protect electronic protected health "
        "information from improper alteration or destruction."
    )
    severity = Severity.HIGH
    remediation_template = (
        "Always use specific where clauses in Model.update() calls to prevent "
        "unintended mass updates. Example: Model.update(data, { where: { id: specificId } })"
    )

    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Any]:
        """Scan for unsafe update operations."""
        # TODO: Implement detection of:
        # Model.update() calls without where clauses or with overly broad where clauses
        # Use find_function_calls to find .update() calls
        # Parse arguments to check for where clause presence and specificity
        # NOTE: For any file_path string matching, use self.normalize_path(file_path)
        # so Windows backslash paths still match patterns like "/routes/".
        return []


# Singleton instance for easy import
in1_rule = IN1Integrity()

__all__ = ["IN1Integrity", "in1_rule"]

# Made with Bob
