"""AC-2: Automatic Logoff - Detect session timeouts exceeding 30 minutes.

45 CFR § 164.312(a)(2)(iii) - Automatic logoff
"""

from __future__ import annotations

from typing import Any

from ..models import Severity
from ..scanner.tree_sitter import find_object_literals, get_node_text
from .base import RuleBase


class AC2SessionTimeout(RuleBase):
    """Detect session configurations with excessive timeout periods."""

    # 30 minutes in milliseconds
    MAX_ALLOWED_MS = 1800000

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
        findings: list[Any] = []

        # Only relevant in middleware / session / config files where express-session is wired up.
        path_lower = self.normalize_path(file_path)
        if not (
            "/middleware/" in path_lower
            or "/config/" in path_lower
            or path_lower.endswith("session.js")
            or path_lower.endswith("session.ts")
            or path_lower.endswith("app.js")
            or path_lower.endswith("server.js")
        ):
            return findings

        source_code = context.get("source_code", "")
        if not source_code:
            for sf in context.get("source_files", []):
                if str(sf.path) == file_path:
                    source_code = sf.text
                    break

        if not source_code:
            return findings

        # Only investigate files that actually pull in express-session — otherwise
        # an unrelated maxAge key (e.g. a cache config) would false-positive.
        if "express-session" not in source_code and "require('express-session')" not in source_code:
            return findings

        # Find all `maxAge: <value>` pairs.
        for prop in find_object_literals(tree, source_code, r"^maxAge$"):
            value_text = prop["value"].strip()
            ms = self._parse_milliseconds(value_text)
            if ms is None:
                continue
            if ms > self.MAX_ALLOWED_MS:
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
                            f"Session cookie maxAge is {ms} ms "
                            f"({ms // 60000} minutes), exceeding the HIPAA-recommended "
                            f"30-minute automatic logoff window."
                        ),
                    )
                )

        return findings

    @staticmethod
    def _parse_milliseconds(value_text: str) -> int | None:
        """Parse simple numeric/arithmetic millisecond expressions.

        Handles bare ints (``86400000``) and simple products
        (``1000 * 60 * 60 * 24``). Anything more complex returns None and is
        left alone — better to under-flag than to mis-parse.
        """
        text = value_text.strip().rstrip(",")
        try:
            return int(text)
        except ValueError:
            pass

        # Only allow a multiplication-of-integers chain.
        if "*" in text and all(
            part.strip().isdigit() for part in text.split("*")
        ):
            result = 1
            for part in text.split("*"):
                result *= int(part.strip())
            return result

        return None


# Singleton instance for easy import
ac2_rule = AC2SessionTimeout()

__all__ = ["AC2SessionTimeout", "ac2_rule"]

# Made with Bob
