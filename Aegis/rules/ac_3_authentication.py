"""AC-3: Person/Entity Authentication - Detect hardcoded credentials.

45 CFR § 164.312(d) - Person or entity authentication
"""

from __future__ import annotations

from typing import Any

from ..models import Severity
from ..scanner.tree_sitter import get_node_text, node_to_line_range
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

    # Identifier names that strongly imply a credential is being checked.
    CREDENTIAL_IDENTIFIERS = {
        "username",
        "user",
        "userid",
        "user_id",
        "login",
        "email",
        "password",
        "passwd",
        "pwd",
        "pass",
        "secret",
        "token",
        "apikey",
        "api_key",
    }

    EQUALITY_OPS = {"==", "==="}

    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Any]:
        """Scan JavaScript file for hardcoded credentials."""
        # Use normalize_path() even though this rule intentionally has no path
        # exclusion — keeps the convention consistent across rules.
        _ = self.normalize_path(file_path)

        findings: list[Any] = []

        source_code = context.get("source_code", "")
        if not source_code:
            for sf in context.get("source_files", []):
                if str(sf.path) == file_path:
                    source_code = sf.text
                    break

        if not source_code:
            return findings

        # Track nodes we've already reported so an outer `&&` doesn't duplicate
        # findings already reported on the inner comparisons.
        reported_lines: set[int] = set()

        def visit(node: Any) -> None:
            if node.type == "binary_expression":
                operator_node = node.child(1)
                op = get_node_text(operator_node, source_code) if operator_node else ""
                if op in self.EQUALITY_OPS:
                    if self._is_credential_string_compare(node, source_code):
                        line_start, line_end = node_to_line_range(node)
                        if line_start not in reported_lines:
                            reported_lines.add(line_start)
                            lines = source_code.split("\n")
                            start_idx = max(line_start - 1, 0)
                            end_idx = min(line_end, len(lines))
                            snippet = "\n".join(lines[start_idx:end_idx])

                            findings.append(
                                self.create_finding(
                                    file_path=file_path,
                                    line_start=line_start,
                                    line_end=line_end,
                                    snippet=snippet,
                                    why=(
                                        "Credential identifier compared against a string "
                                        "literal — hardcoded credentials bypass real "
                                        "authentication and are easily extracted from source."
                                    ),
                                )
                            )

            for child in node.children:
                visit(child)

        visit(tree)
        return findings

    def _is_credential_string_compare(self, node: Any, source_code: str) -> bool:
        """True if one side is a credential identifier and the other is a string literal."""
        left = node.child_by_field_name("left")
        right = node.child_by_field_name("right")
        if left is None or right is None:
            return False

        left_is_cred = self._is_credential_identifier(left, source_code)
        right_is_cred = self._is_credential_identifier(right, source_code)
        left_is_string = self._is_string_literal(left)
        right_is_string = self._is_string_literal(right)

        return (left_is_cred and right_is_string) or (right_is_cred and left_is_string)

    def _is_credential_identifier(self, node: Any, source_code: str) -> bool:
        if node.type == "identifier":
            return get_node_text(node, source_code).lower() in self.CREDENTIAL_IDENTIFIERS
        if node.type == "member_expression":
            prop = node.child_by_field_name("property")
            if prop is not None:
                return get_node_text(prop, source_code).lower() in self.CREDENTIAL_IDENTIFIERS
        return False

    @staticmethod
    def _is_string_literal(node: Any) -> bool:
        # tree-sitter-javascript uses "string" and "template_string" types.
        return node.type in ("string", "template_string")


# Singleton instance for easy import
ac3_rule = AC3Authentication()

__all__ = ["AC3Authentication", "ac3_rule"]

# Made with Bob
