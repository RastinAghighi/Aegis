"""TR-1: Transmission Security - Detect insecure data transmission.

45 CFR § 164.312(e)(1) - Transmission security
"""

from __future__ import annotations

import re
from typing import Any

from ..models import Severity
from ..scanner.tree_sitter import (
    find_object_literals,
    get_node_text,
    node_to_line_range,
)
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

    LOCALHOST_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "::1")

    HTTP_URL_RE = re.compile(r"^http://([^/\s'\"`]+)", re.IGNORECASE)

    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Any]:
        """Scan for ssl:false in db config and http:// URLs in http client code."""
        findings: list[Any] = []

        source_code = context.get("source_code", "")
        if not source_code:
            for sf in context.get("source_files", []):
                if str(sf.path) == file_path:
                    source_code = sf.text
                    break
        if not source_code:
            return findings

        path_lower = self.normalize_path(file_path)

        # Check 1: ssl: false in database config files.
        if self._is_db_config_file(path_lower, source_code):
            findings.extend(self._check_ssl_false(tree, file_path, source_code))

        # Check 2: http:// URLs in files that perform HTTP client calls.
        if self._uses_http_client(source_code):
            findings.extend(self._check_http_urls(tree, file_path, source_code))

        return findings

    def _is_db_config_file(self, path_lower: str, source_code: str) -> bool:
        if "/config/" in path_lower and "database" in path_lower:
            return True
        if path_lower.endswith("database.js") or path_lower.endswith("database.ts"):
            return True
        # Fallback heuristic — file constructs a Sequelize instance.
        return "new Sequelize" in source_code

    def _check_ssl_false(
        self, tree: Any, file_path: str, source_code: str
    ) -> list[Any]:
        findings: list[Any] = []
        for prop in find_object_literals(tree, source_code, r"^ssl$"):
            value = prop["value"].strip().rstrip(",").lower()
            if value in ("false", "'false'", '"false"'):
                lines = source_code.split("\n")
                start_idx = max(prop["line_start"] - 1, 0)
                end_idx = min(prop["line_end"], len(lines))
                snippet = "\n".join(lines[start_idx:end_idx])

                findings.append(
                    self.create_finding(
                        file_path=file_path,
                        line_start=prop["line_start"],
                        line_end=prop["line_end"],
                        snippet=snippet,
                        why=(
                            "Database connection has ssl explicitly disabled. "
                            "PHI flowing to the database is transmitted in cleartext."
                        ),
                    )
                )
        return findings

    @staticmethod
    def _uses_http_client(source_code: str) -> bool:
        return (
            "axios" in source_code
            or "fetch(" in source_code
            or "node-fetch" in source_code
            or "got(" in source_code
            or "request(" in source_code
        )

    def _check_http_urls(
        self, tree: Any, file_path: str, source_code: str
    ) -> list[Any]:
        findings: list[Any] = []
        reported_lines: set[int] = set()

        def visit(node: Any) -> None:
            if node.type in ("string", "template_string"):
                text = get_node_text(node, source_code).strip("\"'`")
                match = self.HTTP_URL_RE.match(text)
                if match:
                    host = match.group(1).split(":")[0].lower()
                    if not any(host == h or host.startswith(h) for h in self.LOCALHOST_HOSTS):
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
                                        f"Insecure http:// URL ('{text}') used in HTTP "
                                        "client code. PHI in flight must travel over "
                                        "TLS — use https:// instead."
                                    ),
                                )
                            )
            for child in node.children:
                visit(child)

        visit(tree)
        return findings


# Singleton instance for easy import
tr1_rule = TR1Transmission()

__all__ = ["TR1Transmission", "tr1_rule"]

# Made with Bob
