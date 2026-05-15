"""JSON report export."""

from __future__ import annotations

import json
from pathlib import Path

from ..models import Report


def render(report: Report, out_path: Path) -> Path:
    """Serialise `report` as pretty-printed JSON to `out_path`."""
    out_path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, default=str),
        encoding="utf-8",
    )
    return out_path
