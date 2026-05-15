"""Rule catalog. One rule per HIPAA control.

Each rule module exports a single `Rule` subclass. The registry below is the
authoritative list of available rules; Bob can iterate over it from MCP.
"""

from .base import Rule, Severity

# Bob: populate this list as you implement rules.
REGISTRY: list[type[Rule]] = []

__all__ = ["Rule", "Severity", "REGISTRY"]
