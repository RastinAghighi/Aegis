"""EN-1: Encryption - Detect unencrypted PHI storage and transmission.

45 CFR § 164.312(a)(2)(iv) - Encryption and decryption
"""

from __future__ import annotations

from typing import Any

from ..models import Severity
from ..scanner.tree_sitter import (
    find_member_assignments,
    find_sequelize_model_fields,
    get_node_text,
)
from .base import RuleBase


class EN1Encryption(RuleBase):
    """Detect PHI stored or transmitted without encryption."""

    rule_id = "EN-1"
    cfr = "164.312(a)(2)(iv)"
    title = "Encryption and Decryption"
    description = (
        "Implement a mechanism to encrypt and decrypt electronic protected health "
        "information."
    )
    severity = Severity.CRITICAL
    remediation_template = (
        "1. For Sequelize models: Use encryption hooks or encrypted field types for PHI fields like SSN.\n"
        "2. For assignments: Encrypt PHI data before storing (e.g., patient.ssn = encrypt(req.body.ssn)).\n"
        "3. Consider using libraries like crypto-js or sequelize-encrypted for field-level encryption."
    )

    # PHI field names that should be encrypted
    PHI_FIELD_NAMES = [
        "ssn",
        "social_security",
        "social_security_number",
        "tax_id",
        "drivers_license",
        "passport",
        "credit_card",
        "bank_account",
        "diagnosis",
        "medical_record",
        "prescription",
        "lab_result",
    ]

    def match_js(
        self, tree: Any, file_path: str, context: dict[str, Any]
    ) -> list[Any]:
        """Scan JavaScript file for unencrypted PHI."""
        findings = []

        source_code = context.get("source_code", "")
        if not source_code:
            # Try to read from source_files in context
            for sf in context.get("source_files", []):
                if str(sf.path) == file_path:
                    source_code = sf.text
                    break

        if not source_code:
            return findings

        # Check 1: Sequelize model definitions with unencrypted PHI fields
        if self._is_model_file(file_path):
            findings.extend(
                self._check_model_fields(tree, file_path, source_code)
            )

        # Check 2: Direct PHI assignments without encryption
        findings.extend(
            self._check_phi_assignments(tree, file_path, source_code)
        )

        return findings

    def _is_model_file(self, file_path: str) -> bool:
        """Check if file is likely a model definition."""
        path_lower = self.normalize_path(file_path)
        return (
            "/models/" in path_lower
            or path_lower.endswith("model.js")
            or path_lower.endswith("model.ts")
        )

    def _check_model_fields(
        self, tree: Any, file_path: str, source_code: str
    ) -> list[Any]:
        """Check Sequelize model fields for unencrypted PHI."""
        findings = []
        fields = find_sequelize_model_fields(tree, source_code)

        for field in fields:
            field_name = field["field_name"].lower()
            
            # Check if it's a PHI field
            if any(phi in field_name for phi in self.PHI_FIELD_NAMES):
                # Check if encryption is mentioned in the field definition
                # Look for keywords like 'encrypt', 'encrypted', 'cipher'
                field_text = get_node_text(field["node"], source_code).lower()
                has_encryption = any(
                    keyword in field_text
                    for keyword in ["encrypt", "cipher", "crypto", "hash"]
                )

                if not has_encryption:
                    lines = source_code.split("\n")
                    start_idx = field["line_start"] - 1
                    end_idx = min(field["line_end"], len(lines))
                    snippet = "\n".join(lines[start_idx:end_idx])

                    finding = self.create_finding(
                        file_path=file_path,
                        line_start=field["line_start"],
                        line_end=field["line_end"],
                        snippet=snippet,
                        why=(
                            f"PHI field '{field['field_name']}' is defined without encryption. "
                            f"Sensitive data should be encrypted at rest."
                        ),
                    )
                    findings.append(finding)

        return findings

    def _check_phi_assignments(
        self, tree: Any, file_path: str, source_code: str
    ) -> list[Any]:
        """Check for direct PHI assignments without encryption."""
        findings = []

        # Build pattern to match PHI field assignments
        phi_pattern = "|".join(self.PHI_FIELD_NAMES)
        assignments = find_member_assignments(tree, source_code, rf"\.({phi_pattern})")

        for assignment in assignments:
            # Check if the value being assigned is encrypted
            value = assignment["value"].lower()
            
            # Look for encryption function calls
            has_encryption = any(
                keyword in value
                for keyword in ["encrypt", "cipher", "crypto", "hash", "bcrypt"]
            )

            # Check if it's reading from req.body (likely plaintext)
            is_plaintext_input = "req.body" in assignment["value"]

            if is_plaintext_input and not has_encryption:
                lines = source_code.split("\n")
                start_idx = assignment["line_start"] - 1
                end_idx = min(assignment["line_end"], len(lines))
                snippet = "\n".join(lines[start_idx:end_idx])

                finding = self.create_finding(
                    file_path=file_path,
                    line_start=assignment["line_start"],
                    line_end=assignment["line_end"],
                    snippet=snippet,
                    why=(
                        f"PHI assignment '{assignment['target']}' stores plaintext data from request. "
                        f"Encrypt sensitive data before storage."
                    ),
                )
                findings.append(finding)

        return findings


# Singleton instance for easy import
en1_rule = EN1Encryption()

__all__ = ["EN1Encryption", "en1_rule"]

# Made with Bob
