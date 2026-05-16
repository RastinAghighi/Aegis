"""IN-1: Integrity - Detect unsafe database update operations.

45 CFR § 164.312(c)(1) - Integrity
"""

from __future__ import annotations

import re
from typing import Any

from ..models import Severity
from ..scanner.tree_sitter import get_node_text, node_to_line_range
from .base import RuleBase


class IN1Integrity(RuleBase):
    """Detect Sequelize Model.update() calls scoped by a foreign key instead of PK."""

    rule_id = "IN-1"
    cfr = "164.312(c)(1)"
    title = "Integrity"
    description = (
        "Implement policies and procedures to protect electronic protected health "
        "information from improper alteration or destruction."
    )
    severity = Severity.HIGH
    remediation_template = (
        "Scope Model.update() to a specific primary key, not a foreign key. "
        "Example: Model.update(data, { where: { id: specificId } }). "
        "A foreign-key where clause (e.g. patient_id) will overwrite every row "
        "owned by that parent — a mass-update violation of PHI integrity."
    )

    # FK identifiers are conventionally `<entity>_id` or `<entity>Id`.
    FK_NAME_RE = re.compile(r"^(?!id$)([a-z][a-z0-9]*_id|[a-z][a-zA-Z0-9]*Id)$")

    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Any]:
        """Scan for Model.update(..., { where: { <fk>: ... } })."""
        # Normalize the path even if we don't currently filter on it — keeps
        # the convention consistent so a future location filter is easy.
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

        reported_lines: set[int] = set()

        def visit(node: Any) -> None:
            if node.type == "call_expression":
                callee = node.child_by_field_name("function")
                if callee and callee.type == "member_expression":
                    prop = callee.child_by_field_name("property")
                    obj = callee.child_by_field_name("object")
                    if (
                        prop
                        and get_node_text(prop, source_code) == "update"
                        and obj
                        and self._looks_like_model(get_node_text(obj, source_code))
                    ):
                        args = node.child_by_field_name("arguments")
                        if args and args.named_child_count >= 2:
                            options = args.named_child(1)
                            fk_keys = self._where_foreign_keys(options, source_code)
                            if fk_keys:
                                line_start, line_end = node_to_line_range(node)
                                if line_start in reported_lines:
                                    return
                                reported_lines.add(line_start)
                                lines = source_code.split("\n")
                                start_idx = max(line_start - 1, 0)
                                end_idx = min(line_end, len(lines))
                                snippet = "\n".join(lines[start_idx:end_idx])

                                model_name = get_node_text(obj, source_code)
                                findings.append(
                                    self.create_finding(
                                        file_path=file_path,
                                        line_start=line_start,
                                        line_end=line_end,
                                        snippet=snippet,
                                        why=(
                                            f"{model_name}.update() is scoped by "
                                            f"foreign key(s) {sorted(fk_keys)} rather "
                                            f"than the primary key 'id'. This mass-updates "
                                            f"every row sharing that parent and risks "
                                            f"overwriting PHI for unrelated records."
                                        ),
                                    )
                                )

            for child in node.children:
                visit(child)

        visit(tree)
        return findings

    @staticmethod
    def _looks_like_model(name: str) -> bool:
        # Sequelize models are conventionally PascalCase identifiers
        # (Patient, Medication, AuditLog). Exclude obvious non-models.
        if not name or not name[0].isupper():
            return False
        if "." in name or "[" in name:
            return False
        return True

    def _where_foreign_keys(self, options_node: Any, source_code: str) -> set[str]:
        """If options has a `where` object, return any non-PK keys that look like FKs."""
        if options_node.type != "object":
            return set()

        where_obj = None
        for pair in options_node.children:
            if pair.type != "pair":
                continue
            key_node = pair.child_by_field_name("key")
            value_node = pair.child_by_field_name("value")
            if not key_node or not value_node:
                continue
            if get_node_text(key_node, source_code).strip("\"'") == "where":
                where_obj = value_node
                break

        if where_obj is None or where_obj.type != "object":
            return set()

        fk_keys: set[str] = set()
        for child in where_obj.children:
            # Standard `key: value` pair.
            if child.type == "pair":
                key_node = child.child_by_field_name("key")
                if not key_node:
                    continue
                key = get_node_text(key_node, source_code).strip("\"'")
            # ES2015 shorthand: `{ patient_id }` — the identifier itself is the property.
            elif child.type == "shorthand_property_identifier":
                key = get_node_text(child, source_code)
            else:
                continue

            if self.FK_NAME_RE.match(key):
                fk_keys.add(key)
        return fk_keys


# Singleton instance for easy import
in1_rule = IN1Integrity()

__all__ = ["IN1Integrity", "in1_rule"]

# Made with Bob
