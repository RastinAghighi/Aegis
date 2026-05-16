"""AC-1: Access Control - Detect Express routes touching PHI without auth middleware.

45 CFR § 164.312(a)(1) - Access control
"""

from __future__ import annotations

from typing import Any

from ..models import Severity
from ..scanner.tree_sitter import find_route_handlers, get_node_text
from .base import RuleBase


class AC1AccessControl(RuleBase):
    """Detect Express routes that access PHI without authentication middleware."""

    rule_id = "AC-1"
    cfr = "164.312(a)(1)"
    title = "Access Control"
    description = (
        "Implement technical policies and procedures for electronic information "
        "systems that maintain electronic protected health information to allow "
        "access only to those persons or software programs that have been granted "
        "access rights."
    )
    severity = Severity.CRITICAL
    remediation_template = (
        "Add authentication middleware (e.g., requireAuth, authenticate, isAuthenticated) "
        "to all routes that access Protected Health Information (PHI). "
        "Example: router.get('/patients/:id', requireAuth, async (req, res) => { ... })"
    )

    # Routes that typically access PHI
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

    # Common auth middleware names
    AUTH_MIDDLEWARE_NAMES = [
        "requireAuth",
        "authenticate",
        "isAuthenticated",
        "checkAuth",
        "verifyAuth",
        "ensureAuth",
        "authRequired",
        "protect",
        "authorize",
    ]

    # Auth-flow routes that inherently can't require auth (the user is acquiring
    # a session here) — flagging them as PHI access would be a false positive.
    EXCLUDE_AUTH_ROUTES = {
        "/login",
        "/logout",
        "/register",
        "/signup",
        "/auth",
        "/signin",
        "/signout",
    }

    # Files that exist solely to handle auth flows. Their routes are not PHI
    # access points even if they live in /routes/.
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

    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Any]:
        """Scan JavaScript file for unprotected PHI routes."""
        findings = []

        # Only scan route files
        if not self._is_route_file(file_path):
            return findings

        source_code = context.get("source_code", "")
        if not source_code:
            # Try to read from source_files in context
            for sf in context.get("source_files", []):
                if str(sf.path) == file_path:
                    source_code = sf.text
                    break

        if not source_code:
            return findings

        # Find all route handlers
        routes = find_route_handlers(tree, source_code)

        # If the route file itself is PHI-named (e.g., routes/patients.js), every
        # route inside touches PHI even though the local paths are relative ("/", "/:id").
        file_is_phi = self._is_phi_route(file_path)

        for route in routes:
            # Skip auth-flow routes — they cannot require auth by definition.
            if self._is_auth_route(route["path"]):
                continue

            # Check if route path or containing file suggests PHI access
            if self._is_phi_route(route["path"]) or file_is_phi:
                # Check if route has auth middleware
                has_auth = any(
                    mw in self.AUTH_MIDDLEWARE_NAMES for mw in route["middleware"]
                )

                if not has_auth:
                    # Extract snippet
                    lines = source_code.split("\n")
                    start_idx = route["line_start"] - 1
                    end_idx = min(route["line_end"], len(lines))
                    snippet = "\n".join(lines[start_idx:end_idx])

                    finding = self.create_finding(
                        file_path=file_path,
                        line_start=route["line_start"],
                        line_end=route["line_end"],
                        snippet=snippet,
                        why=(
                            f"Route {route['method'].upper()} {route['path']} accesses PHI "
                            f"but has no authentication middleware. Found middleware: "
                            f"{route['middleware'] or 'none'}"
                        ),
                    )
                    findings.append(finding)

        return findings

    def _is_route_file(self, file_path: str) -> bool:
        """Check if file is likely a route definition file."""
        path_lower = self.normalize_path(file_path)

        # Auth-machinery files don't define PHI routes even when they live
        # alongside the rest of the route layer.
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

    def _is_phi_route(self, path: str) -> bool:
        """Check if route path (or file path) suggests PHI access."""
        path_lower = self.normalize_path(path)
        return any(pattern in path_lower for pattern in self.PHI_ROUTE_PATTERNS)

    def _is_auth_route(self, path: str) -> bool:
        """Check if a route path is an auth flow (login, logout, signup, ...)."""
        path_lower = self.normalize_path(path).rstrip("/")
        if not path_lower:
            return False
        # Match exact paths like "/login" and prefixes like "/auth/...".
        for excluded in self.EXCLUDE_AUTH_ROUTES:
            if path_lower == excluded or path_lower.startswith(excluded + "/"):
                return True
        return False


# Singleton instance for easy import
ac1_rule = AC1AccessControl()

__all__ = ["AC1AccessControl", "ac1_rule"]

# Made with Bob
