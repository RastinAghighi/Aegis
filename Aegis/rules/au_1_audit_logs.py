"""AU-1: Audit Controls - Detect missing audit logging.

45 CFR § 164.312(b) - Audit controls
"""

from __future__ import annotations

from typing import Any

from ..models import Severity
from ..scanner.tree_sitter import (
    find_route_handlers,
    get_node_text,
    node_to_line_range,
)
from .base import RuleBase


class AU1AuditLogs(RuleBase):
    """Detect PHI route handlers that never call AuditLog.create()."""

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

    PHI_ROUTE_PATTERNS = [
        r"/patients",
        r"/patient",
        r"/medical",
        r"/health",
        r"/diagnosis",
        r"/medication",
        r"/appointment",
        r"/prescription",
        r"/lab",
        r"/test",
        r"/treatment",
    ]

    # Reuse AC-1's auth-route exclusions verbatim.
    EXCLUDE_AUTH_ROUTES = {
        "/login",
        "/logout",
        "/register",
        "/signup",
        "/auth",
        "/signin",
        "/signout",
    }
    EXCLUDE_AUTH_FILES = {
        "auth.js",
        "auth.ts",
        "login.js",
        "login.ts",
        "register.js",
        "register.ts",
        "signup.js",
        "signup.ts",
        "signin.js",
        "signin.ts",
    }

    AUDIT_LOG_CALL = "AuditLog.create"

    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Any]:
        """Scan PHI-touching route handlers for missing audit log writes."""
        findings: list[Any] = []

        if not self._is_route_file(file_path):
            return findings

        # Cross-file precondition: only fire if the project actually has an
        # AuditLog model. Otherwise the absence of AuditLog.create() is just
        # "this project doesn't use audit logs at all" — not a rule violation
        # we can pin to one route.
        if not self._project_has_audit_log_model(context):
            return findings

        source_code = self._get_source(file_path, context)
        if not source_code:
            return findings

        routes = find_route_handlers(tree, source_code)
        file_is_phi = self._is_phi_path(file_path)

        for route in routes:
            if self._is_auth_route(route["path"]):
                continue
            if not (file_is_phi or self._is_phi_path(route["path"])):
                continue

            handler_text = get_node_text(route["handler_node"], source_code)
            if self.AUDIT_LOG_CALL in handler_text:
                continue

            line_start, line_end = node_to_line_range(route["handler_node"])
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
                        f"PHI route {route['method'].upper()} {route['path']} "
                        f"does not call AuditLog.create(). Every read/write of PHI "
                        f"must produce an audit log entry."
                    ),
                )
            )

        return findings

    def _get_source(self, file_path: str, context: dict[str, Any]) -> str:
        source_code = context.get("source_code", "")
        if source_code:
            return source_code
        for sf in context.get("source_files", []):
            if str(sf.path) == file_path:
                return sf.text
        return ""

    def _project_has_audit_log_model(self, context: dict[str, Any]) -> bool:
        for raw_path in context.get("all_files", []):
            path = self.normalize_path(raw_path)
            if "/models/" in path and "auditlog" in path.rsplit("/", 1)[-1]:
                return True
        return False

    def _is_route_file(self, file_path: str) -> bool:
        path_lower = self.normalize_path(file_path)
        basename = path_lower.rsplit("/", 1)[-1]
        if basename in self.EXCLUDE_AUTH_FILES:
            return False
        return (
            "/routes/" in path_lower
            or "/api/" in path_lower
            or path_lower.endswith("routes.js")
            or path_lower.endswith("routes.ts")
            or path_lower.endswith("router.js")
            or path_lower.endswith("router.ts")
        )

    def _is_phi_path(self, path: str) -> bool:
        path_lower = self.normalize_path(path)
        return any(pattern in path_lower for pattern in self.PHI_ROUTE_PATTERNS)

    def _is_auth_route(self, path: str) -> bool:
        path_lower = self.normalize_path(path).rstrip("/")
        if not path_lower:
            return False
        for excluded in self.EXCLUDE_AUTH_ROUTES:
            if path_lower == excluded or path_lower.startswith(excluded + "/"):
                return True
        return False


# Singleton instance for easy import
au1_rule = AU1AuditLogs()

__all__ = ["AU1AuditLogs", "au1_rule"]

# Made with Bob
