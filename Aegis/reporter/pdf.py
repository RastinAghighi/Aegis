"""PDF report generation using ReportLab.

TODO (Bob):
  - cover page (target, generated_at, severity counts)
  - per-rule sections with CFR text and remediation
  - per-finding evidence block with snippet and file:line ref
  - styled with reportlab.platypus (SimpleDocTemplate, Paragraph, Table)
"""

from __future__ import annotations

from pathlib import Path

from ..models import Report


def render(report: Report, out_path: Path) -> Path:
    """Render `report` to a PDF at `out_path`. Returns the output path."""
    raise NotImplementedError("PDF rendering not implemented yet")
