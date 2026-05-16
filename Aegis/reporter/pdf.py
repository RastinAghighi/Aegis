"""PDF report generation using ReportLab.

Produces an audit-ready report styled for a Big 4 firm aesthetic:
  - Cover page with Aegis wordmark
  - Executive summary with severity table and risk score
  - Findings index
  - Per-finding detail pages (half-page for CRITICAL/HIGH, condensed otherwise)
  - Appendix with full CFR text for every rule and scan metadata
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from ..models import Report, Severity

# Palette
SLATE_900 = colors.HexColor("#0F172A")
SLATE_700 = colors.HexColor("#334155")
SLATE_500 = colors.HexColor("#64748B")
SLATE_300 = colors.HexColor("#CBD5E1")
SLATE_200 = colors.HexColor("#E2E8F0")
SLATE_100 = colors.HexColor("#F1F5F9")
SLATE_50 = colors.HexColor("#F8FAFC")
ROSE_600 = colors.HexColor("#E11D48")
ROSE_50 = colors.HexColor("#FFF1F2")
AMBER_600 = colors.HexColor("#D97706")
AMBER_50 = colors.HexColor("#FFFBEB")
YELLOW_600 = colors.HexColor("#CA8A04")
SKY_600 = colors.HexColor("#0284C7")
EMERALD_600 = colors.HexColor("#059669")
WHITE = colors.white

SEVERITY_COLOR = {
    "CRITICAL": ROSE_600,
    "HIGH": AMBER_600,
    "MEDIUM": YELLOW_600,
    "LOW": SKY_600,
}

SEVERITY_FILL = {
    "CRITICAL": ROSE_50,
    "HIGH": AMBER_50,
    "MEDIUM": colors.HexColor("#FEFCE8"),
    "LOW": colors.HexColor("#F0F9FF"),
}

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

PAGE_WIDTH, PAGE_HEIGHT = LETTER
MARGIN = 1.0 * inch
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN


# ----- Scanner version helpers ----------------------------------------------

def _scanner_version() -> str:
    """Read package version from pyproject.toml; fall back to package metadata."""
    try:
        pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
        if pyproject.exists():
            for line in pyproject.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("version"):
                    parts = stripped.split("=", 1)
                    if len(parts) == 2:
                        return parts[1].strip().strip('"').strip("'")
    except Exception:
        pass
    try:
        from importlib.metadata import version

        return version("aegis")
    except Exception:
        return "0.1.0"


# ----- Custom flowables ------------------------------------------------------

class HRule(Flowable):
    """A thin horizontal divider."""

    def __init__(self, width: float, color=SLATE_200, thickness: float = 0.5) -> None:
        super().__init__()
        self.width = width
        self.color = color
        self.thickness = thickness

    def wrap(self, _aw, _ah):
        return self.width, self.thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


class Wordmark(Flowable):
    """The 'AEGIS' wordmark: Helvetica Bold, all-caps, letter-spaced."""

    def __init__(self, text: str = "AEGIS", size: float = 36, tracking: float = 8.0,
                 color=SLATE_900) -> None:
        super().__init__()
        self.text = text.upper()
        self.size = size
        self.tracking = tracking
        self.color = color

    def wrap(self, aw, _ah):
        self._aw = aw
        return aw, self.size * 1.4

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.setFont("Helvetica-Bold", self.size)
        # Measure width with tracking
        total_w = 0.0
        widths = []
        for ch in self.text:
            w = c.stringWidth(ch, "Helvetica-Bold", self.size)
            widths.append(w)
            total_w += w
        total_w += self.tracking * (len(self.text) - 1)
        x = (self._aw - total_w) / 2.0
        y = 0
        for ch, w in zip(self.text, widths):
            c.drawString(x, y, ch)
            x += w + self.tracking


class RiskScoreBox(Flowable):
    """Large boxed risk score with formula underneath."""

    def __init__(self, score: int, formula: str, width: float, height: float = 1.6 * inch) -> None:
        super().__init__()
        self.score = score
        self.formula = formula
        self.width = width
        self.height = height

    def wrap(self, _aw, _ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        # Box
        c.setStrokeColor(SLATE_200)
        c.setFillColor(SLATE_50)
        c.setLineWidth(0.75)
        c.rect(0, 0, self.width, self.height, stroke=1, fill=1)

        # "RISK SCORE" label
        c.setFillColor(SLATE_500)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(0.2 * inch, self.height - 0.3 * inch, "RISK SCORE")

        # Big score
        score_text = f"{self.score}"
        c.setFont("Helvetica-Bold", 56)
        # Color by score: green high, amber mid, red low
        if self.score >= 80:
            c.setFillColor(EMERALD_600)
        elif self.score >= 50:
            c.setFillColor(AMBER_600)
        else:
            c.setFillColor(ROSE_600)
        c.drawString(0.2 * inch, self.height - 1.05 * inch, score_text)
        # Suffix
        c.setFillColor(SLATE_500)
        c.setFont("Helvetica", 18)
        suffix_x = 0.2 * inch + c.stringWidth(score_text, "Helvetica-Bold", 56) + 4
        c.drawString(suffix_x, self.height - 0.95 * inch, "/ 100")

        # Formula
        c.setFillColor(SLATE_500)
        c.setFont("Helvetica", 7.5)
        c.drawString(0.2 * inch, 0.22 * inch, self.formula)


class SeverityBadge(Flowable):
    """Small colored chip showing the severity."""

    def __init__(self, severity: str, width: float = 0.95 * inch, height: float = 0.22 * inch) -> None:
        super().__init__()
        self.severity = severity
        self.width = width
        self.height = height

    def wrap(self, _aw, _ah):
        return self.width, self.height

    def draw(self):
        c = self.canv
        fill = SEVERITY_COLOR.get(self.severity, SLATE_500)
        c.setFillColor(fill)
        c.setStrokeColor(fill)
        c.roundRect(0, 0, self.width, self.height, 3, stroke=0, fill=1)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 8)
        text_w = c.stringWidth(self.severity, "Helvetica-Bold", 8)
        c.drawString((self.width - text_w) / 2.0, (self.height - 8) / 2.0 + 1.5, self.severity)


# ----- Page callbacks --------------------------------------------------------

def _draw_cover_background(canvas, _doc) -> None:
    # Thin top + bottom rule for cover
    canvas.saveState()
    canvas.setStrokeColor(SLATE_300)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, PAGE_HEIGHT - MARGIN + 0.1 * inch,
                PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN + 0.1 * inch)
    canvas.line(MARGIN, MARGIN - 0.1 * inch,
                PAGE_WIDTH - MARGIN, MARGIN - 0.1 * inch)
    # Bottom byline
    canvas.setFillColor(SLATE_500)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(
        PAGE_WIDTH / 2.0, MARGIN - 0.3 * inch,
        "Generated by Aegis  ·  Powered by IBM Bob",
    )
    canvas.restoreState()


def _draw_body_chrome(canvas, doc) -> None:
    canvas.saveState()
    # Header rule
    canvas.setStrokeColor(SLATE_200)
    canvas.setLineWidth(0.4)
    canvas.line(MARGIN, PAGE_HEIGHT - MARGIN + 0.35 * inch,
                PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN + 0.35 * inch)
    # Header text
    canvas.setFillColor(SLATE_500)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(MARGIN, PAGE_HEIGHT - MARGIN + 0.45 * inch,
                      "HIPAA Technical Safeguards Audit Report")
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(SLATE_700)
    canvas.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN + 0.45 * inch,
                           "AEGIS")

    # Footer rule
    canvas.setStrokeColor(SLATE_200)
    canvas.setLineWidth(0.4)
    canvas.line(MARGIN, MARGIN - 0.35 * inch,
                PAGE_WIDTH - MARGIN, MARGIN - 0.35 * inch)
    # Footer text — page number right
    canvas.setFillColor(SLATE_500)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(MARGIN, MARGIN - 0.5 * inch,
                      "Generated by Aegis  ·  Powered by IBM Bob")
    canvas.drawRightString(PAGE_WIDTH - MARGIN, MARGIN - 0.5 * inch,
                           f"Page {doc.page}")
    canvas.restoreState()


# ----- Styles ----------------------------------------------------------------

def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}

    styles["CoverTitle"] = ParagraphStyle(
        "CoverTitle",
        parent=base["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=SLATE_900,
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    styles["CoverSubtitle"] = ParagraphStyle(
        "CoverSubtitle",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=SLATE_500,
        alignment=TA_CENTER,
    )
    styles["CoverMeta"] = ParagraphStyle(
        "CoverMeta",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=14,
        textColor=SLATE_700,
        alignment=TA_CENTER,
    )
    styles["H1"] = ParagraphStyle(
        "H1",
        parent=base["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=SLATE_700,
        spaceAfter=10,
        spaceBefore=0,
    )
    styles["H2"] = ParagraphStyle(
        "H2",
        parent=base["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=SLATE_700,
        spaceAfter=6,
        spaceBefore=10,
    )
    styles["H3"] = ParagraphStyle(
        "H3",
        parent=base["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=SLATE_700,
        spaceAfter=4,
        spaceBefore=8,
    )
    styles["Body"] = ParagraphStyle(
        "Body",
        parent=base["BodyText"],
        fontName="Times-Roman",
        fontSize=10.5,
        leading=15,
        textColor=SLATE_900,
        alignment=TA_LEFT,
        spaceAfter=6,
    )
    styles["BodyMuted"] = ParagraphStyle(
        "BodyMuted",
        parent=styles["Body"],
        textColor=SLATE_500,
        fontSize=9.5,
        leading=13,
    )
    styles["CFRBanner"] = ParagraphStyle(
        "CFRBanner",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=SLATE_900,
        spaceAfter=2,
    )
    styles["RuleTitle"] = ParagraphStyle(
        "RuleTitle",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=SLATE_900,
        spaceAfter=2,
    )
    styles["FileLoc"] = ParagraphStyle(
        "FileLoc",
        parent=base["Normal"],
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        textColor=SLATE_700,
        spaceAfter=4,
    )
    styles["Mono"] = ParagraphStyle(
        "Mono",
        parent=base["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10.5,
        textColor=SLATE_900,
        spaceAfter=0,
        spaceBefore=0,
    )
    styles["MonoMuted"] = ParagraphStyle(
        "MonoMuted",
        parent=styles["Mono"],
        textColor=SLATE_500,
    )
    styles["FieldLabel"] = ParagraphStyle(
        "FieldLabel",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=SLATE_500,
        spaceAfter=2,
        spaceBefore=4,
    )
    styles["FieldValue"] = ParagraphStyle(
        "FieldValue",
        parent=base["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=14,
        textColor=SLATE_900,
        spaceAfter=4,
    )
    styles["TableHeader"] = ParagraphStyle(
        "TableHeader",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=WHITE,
    )
    styles["TableCell"] = ParagraphStyle(
        "TableCell",
        parent=base["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=SLATE_900,
    )
    styles["TableCellMono"] = ParagraphStyle(
        "TableCellMono",
        parent=base["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=SLATE_900,
    )
    return styles


# ----- Helpers ---------------------------------------------------------------

def _escape(text: str) -> str:
    """Escape for ReportLab Paragraph mini-HTML."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _short_id(finding_id: str) -> str:
    return finding_id.replace("-", "")[:8]


def _rel_file(path: str, target: str) -> str:
    """Render the file path relative to the scan target when possible."""
    try:
        p = Path(path).resolve()
        t = Path(target).resolve()
        rel = p.relative_to(t)
        return str(rel).replace("\\", "/")
    except Exception:
        return path.replace("\\", "/")


def _code_block(snippet: str, styles: dict[str, ParagraphStyle],
                width: float, max_lines: int = 14) -> Flowable:
    """Render a code excerpt inside a bordered, slate-tinted table cell."""
    if not snippet:
        snippet = "(no snippet available)"
    lines = snippet.splitlines() or [snippet]
    if len(lines) > max_lines:
        lines = lines[: max_lines - 1] + [f"... ({len(snippet.splitlines()) - max_lines + 1} more lines)"]
    # Render each line as its own Paragraph so very long lines wrap.
    paras = []
    for ln in lines:
        # Replace tabs with 4 spaces for stable rendering
        ln = ln.replace("\t", "    ")
        # Use non-breaking spaces for leading indent so wrapping preserves it
        stripped = ln.lstrip(" ")
        indent = len(ln) - len(stripped)
        text = ("&nbsp;" * indent) + _escape(stripped)
        if not text:
            text = "&nbsp;"
        paras.append(Paragraph(text, styles["Mono"]))
    tbl = Table([[paras]], colWidths=[width])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SLATE_50),
        ("BOX", (0, 0), (-1, -1), 0.5, SLATE_200),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tbl


def _format_remediation(remediation: str, cfr_section: str) -> str:
    """Prepend a CFR-cited comment, plain text for embedding in code block."""
    header = f"// 45 CFR § {cfr_section} — recommended remediation"
    return header + "\n" + remediation.strip()


# ----- Section builders ------------------------------------------------------

def _cover_story(report: Report, styles: dict[str, ParagraphStyle]) -> list:
    target_display = str(report.target).replace("\\", "/")
    when = report.generated_at.astimezone().strftime("%B %d, %Y · %H:%M %Z").strip()
    if when.endswith("·"):
        when = report.generated_at.astimezone().strftime("%B %d, %Y · %H:%M")

    story: list = []
    story.append(Spacer(1, 1.4 * inch))
    story.append(Wordmark("AEGIS", size=42, tracking=10, color=SLATE_900))
    story.append(Spacer(1, 0.08 * inch))
    story.append(Paragraph(
        "<font color='#64748B'>HIPAA TECHNICAL SAFEGUARDS AUDIT</font>",
        ParagraphStyle("cap", parent=styles["CoverMeta"], fontSize=8.5,
                       fontName="Helvetica-Bold", alignment=TA_CENTER),
    ))
    story.append(Spacer(1, 1.0 * inch))
    story.append(Paragraph("HIPAA Technical Safeguards", styles["CoverTitle"]))
    story.append(Paragraph("Audit Report", styles["CoverTitle"]))
    story.append(Spacer(1, 0.35 * inch))
    # Centered hairline divider
    divider = Table([[""]], colWidths=[2.0 * inch], rowHeights=[0.01 * inch])
    divider.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.75, SLATE_300),
    ]))
    centered_divider = Table([[divider]], colWidths=[CONTENT_WIDTH])
    centered_divider.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(centered_divider)
    story.append(Spacer(1, 0.35 * inch))
    story.append(Paragraph(
        f"<b>Target</b><br/><font face='Courier' size='10'>{_escape(target_display)}</font>",
        styles["CoverSubtitle"],
    ))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph(f"<b>Scan date</b><br/>{_escape(when)}", styles["CoverSubtitle"]))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph(
        f"<b>Findings</b><br/>{len(report.findings)} total &nbsp;·&nbsp; Risk Score {report.risk_score}/100",
        styles["CoverSubtitle"],
    ))
    return story


def _exec_summary_story(report: Report, styles: dict[str, ParagraphStyle]) -> list:
    counts = report.counts_by_severity
    total = len(report.findings)

    story: list = []
    story.append(Paragraph("Executive Summary", styles["H1"]))
    story.append(HRule(CONTENT_WIDTH, SLATE_200, 0.75))
    story.append(Spacer(1, 0.18 * inch))

    # Summary paragraph
    risk = report.risk_score
    if total == 0:
        narrative = (
            "The Aegis scanner found no HIPAA Technical Safeguards violations in the codebase. "
            "All seven controls (Access Control, Session Timeout, Authentication, Audit Logs, "
            "Encryption, Integrity, and Transmission Security) reported clean."
        )
    else:
        sev_phrase = []
        for s in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            if counts[s]:
                sev_phrase.append(f"{counts[s]} {s.lower()}")
        narrative = (
            f"The Aegis scanner identified {total} potential HIPAA Technical Safeguards "
            f"violation{'s' if total != 1 else ''} in the codebase "
            f"({', '.join(sev_phrase)}). The aggregate risk score is "
            f"{risk}/100. Critical and high findings should be remediated before any environment "
            "handling Protected Health Information is exposed to end users. Each finding below "
            "cites the controlling 45 CFR §164.312 provision and includes prescriptive "
            "remediation guidance."
        )
    story.append(Paragraph(narrative, styles["Body"]))
    story.append(Spacer(1, 0.2 * inch))

    # Two-column: severity table on left, risk box on right
    sev_rows = [
        [Paragraph("Severity", styles["TableHeader"]),
         Paragraph("Count", styles["TableHeader"])],
    ]
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        sev_rows.append([
            Paragraph(
                f"<font color='{SEVERITY_COLOR[sev].hexval()}'><b>●</b></font>&nbsp;&nbsp;{sev}",
                styles["TableCell"],
            ),
            Paragraph(f"<b>{counts[sev]}</b>", styles["TableCell"]),
        ])
    sev_rows.append([
        Paragraph("<b>Total</b>", styles["TableCell"]),
        Paragraph(f"<b>{total}</b>", styles["TableCell"]),
    ])
    sev_table = Table(sev_rows, colWidths=[1.7 * inch, 0.8 * inch])
    sev_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SLATE_700),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, SLATE_200),
        ("LINEBELOW", (0, -2), (-1, -2), 0.5, SLATE_300),
        ("BACKGROUND", (0, -1), (-1, -1), SLATE_50),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [WHITE, SLATE_50]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    risk_box = RiskScoreBox(
        report.risk_score,
        "max(0, 100 − (10×crit + 5×high + 2×med + 1×low))",
        width=3.0 * inch,
        height=1.7 * inch,
    )

    split = Table(
        [[sev_table, risk_box]],
        colWidths=[2.7 * inch, 3.6 * inch],
    )
    split.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 0.3 * inch),
        ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(split)
    story.append(Spacer(1, 0.25 * inch))

    # Rule coverage line
    from ..rules import ALL_RULES
    rules_with_hits = {f.rule_id for f in report.findings}
    story.append(Paragraph("Rule Coverage", styles["H3"]))
    coverage_lines = []
    for r in ALL_RULES:
        hit_count = sum(1 for f in report.findings if f.rule_id == r.rule_id)
        marker = "●" if hit_count else "○"
        color_hex = SEVERITY_COLOR[r.severity.value].hexval() if hit_count else SLATE_300.hexval()
        coverage_lines.append(
            f"<font color='{color_hex}'>{marker}</font>&nbsp; "
            f"<b>{r.rule_id}</b> &nbsp; {_escape(r.title)} "
            f"&nbsp;<font color='#64748B'>· 45 CFR §{r.cfr} · "
            f"{hit_count} finding{'s' if hit_count != 1 else ''}</font>"
        )
    story.append(Paragraph("<br/>".join(coverage_lines), styles["BodyMuted"]))
    return story


def _index_story(report: Report, styles: dict[str, ParagraphStyle]) -> list:
    story: list = []
    story.append(Paragraph("Findings Index", styles["H1"]))
    story.append(HRule(CONTENT_WIDTH, SLATE_200, 0.75))
    story.append(Spacer(1, 0.15 * inch))

    if not report.findings:
        story.append(Paragraph("No findings to report.", styles["Body"]))
        return story

    sorted_findings = sorted(
        report.findings,
        key=lambda f: (SEVERITY_ORDER.get(f.severity.value, 99),
                       _rel_file(f.evidence.file, report.target).lower(),
                       f.evidence.line_start),
    )

    header = [
        Paragraph("ID", styles["TableHeader"]),
        Paragraph("Rule", styles["TableHeader"]),
        Paragraph("CFR", styles["TableHeader"]),
        Paragraph("Severity", styles["TableHeader"]),
        Paragraph("File:Line", styles["TableHeader"]),
    ]
    rows = [header]
    for f in sorted_findings:
        sev = f.severity.value
        loc = f"{_rel_file(f.evidence.file, report.target)}:{f.evidence.line_start}"
        rows.append([
            Paragraph(f"<font face='Courier' size='7.5'>{_short_id(f.id)}</font>",
                      styles["TableCell"]),
            Paragraph(f"<b>{f.rule_id}</b> &nbsp; {_escape(f.rule_title)}", styles["TableCell"]),
            Paragraph(f"§{_escape(f.cfr.section)}", styles["TableCellMono"]),
            Paragraph(
                f"<font color='{SEVERITY_COLOR[sev].hexval()}'><b>●</b></font>&nbsp;"
                f"<font size='7.5'>{sev}</font>",
                styles["TableCell"],
            ),
            Paragraph(f"<font face='Courier' size='7.5'>{_escape(loc)}</font>",
                      styles["TableCell"]),
        ])

    col_widths = [
        0.8 * inch,   # ID
        1.7 * inch,   # Rule
        0.95 * inch,  # CFR
        1.0 * inch,   # Severity
        CONTENT_WIDTH - (0.8 + 1.7 + 0.95 + 1.0) * inch,  # File:Line
    ]
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SLATE_700),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SLATE_50]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, SLATE_200),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, SLATE_200),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)
    return story


def _finding_block(f, report: Report, styles: dict[str, ParagraphStyle],
                   *, condensed: bool) -> Flowable:
    """Render a single finding as a self-contained block."""
    sev = f.severity.value
    accent = SEVERITY_COLOR.get(sev, SLATE_500)
    fill = SEVERITY_FILL.get(sev, SLATE_50)

    # Banner row: CFR + severity badge
    cfr_banner = Paragraph(
        f"<font color='{SLATE_900.hexval()}'>45 CFR § {_escape(f.cfr.section)}</font>",
        styles["CFRBanner"],
    )
    badge = SeverityBadge(sev)
    banner = Table([[cfr_banner, badge]], colWidths=[CONTENT_WIDTH - 1.05 * inch, 1.0 * inch])
    banner.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    body: list = [
        banner,
        Spacer(1, 0.04 * inch),
        Paragraph(f"{_escape(f.rule_title)} &nbsp;<font color='#64748B' size='9'>"
                  f"· {f.rule_id} · ID {_short_id(f.id)}</font>",
                  styles["RuleTitle"]),
        Paragraph(
            f"<font color='#334155'>"
            f"{_escape(_rel_file(f.evidence.file, report.target))}:"
            f"{f.evidence.line_start}–{f.evidence.line_end}"
            f"</font>",
            styles["FileLoc"],
        ),
    ]

    max_lines_evidence = 10 if condensed else 14
    body.append(Paragraph("EVIDENCE", styles["FieldLabel"]))
    body.append(_code_block(f.evidence.snippet, styles, CONTENT_WIDTH - 0.4 * inch,
                            max_lines=max_lines_evidence))

    body.append(Paragraph("WHY THIS IS A VIOLATION", styles["FieldLabel"]))
    body.append(Paragraph(_escape(f.evidence.why), styles["FieldValue"]))

    if not condensed:
        body.append(Paragraph("RECOMMENDED REMEDIATION", styles["FieldLabel"]))
        rem_text = _format_remediation(f.remediation, f.cfr.section)
        body.append(_code_block(rem_text, styles, CONTENT_WIDTH - 0.4 * inch,
                                max_lines=10))
    else:
        body.append(Paragraph("REMEDIATION", styles["FieldLabel"]))
        body.append(Paragraph(_escape(f.remediation), styles["FieldValue"]))

    # Wrap with a left accent bar via a single-cell table with LINEBEFORE
    inner = Table([[body]], colWidths=[CONTENT_WIDTH])
    inner.setStyle(TableStyle([
        ("LINEBEFORE", (0, 0), (0, 0), 3, accent),
        ("BACKGROUND", (0, 0), (-1, -1), fill),
        ("BOX", (0, 0), (-1, -1), 0.4, SLATE_200),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return KeepTogether(inner)


def _findings_detail_story(report: Report, styles: dict[str, ParagraphStyle]) -> list:
    story: list = []
    if not report.findings:
        return story

    story.append(Paragraph("Findings Detail", styles["H1"]))
    story.append(HRule(CONTENT_WIDTH, SLATE_200, 0.75))
    story.append(Spacer(1, 0.15 * inch))

    sorted_findings = sorted(
        report.findings,
        key=lambda f: (SEVERITY_ORDER.get(f.severity.value, 99),
                       _rel_file(f.evidence.file, report.target).lower(),
                       f.evidence.line_start),
    )

    current_sev: str | None = None
    for f in sorted_findings:
        sev = f.severity.value
        condensed = sev in ("MEDIUM", "LOW")
        block = _finding_block(f, report, styles, condensed=condensed)
        if sev != current_sev:
            current_sev = sev
            count_for_sev = sum(1 for x in sorted_findings if x.severity.value == sev)
            heading = Paragraph(
                f"<font color='{SEVERITY_COLOR[sev].hexval()}'>{sev}</font> "
                f"<font color='#64748B' size='9'>"
                f"· {count_for_sev} finding{'s' if count_for_sev != 1 else ''}"
                f"</font>",
                styles["H2"],
            )
            # Keep the section heading with its first finding so we never
            # orphan the heading at the bottom of a page.
            story.append(Spacer(1, 0.1 * inch))
            story.append(KeepTogether([heading, Spacer(1, 0.06 * inch), block]))
        else:
            story.append(block)
        story.append(Spacer(1, 0.18 * inch))
    return story


def _appendix_story(report: Report, styles: dict[str, ParagraphStyle]) -> list:
    from ..rules import ALL_RULES

    story: list = []
    story.append(Paragraph("Appendix A · Rule Catalogue", styles["H1"]))
    story.append(HRule(CONTENT_WIDTH, SLATE_200, 0.75))
    story.append(Spacer(1, 0.15 * inch))

    for r in ALL_RULES:
        sev = r.severity.value
        accent = SEVERITY_COLOR[sev]
        header = Paragraph(
            f"<b>{r.rule_id}</b> &nbsp; {_escape(r.title)} "
            f"<font color='#64748B'>· 45 CFR § {_escape(r.cfr)}</font>",
            styles["H3"],
        )
        badge = SeverityBadge(sev)
        row = Table([[header, badge]],
                    colWidths=[CONTENT_WIDTH - 1.05 * inch, 1.0 * inch])
        row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        block = [
            row,
            Paragraph(_escape(r.description), styles["Body"]),
            Paragraph("REMEDIATION GUIDANCE", styles["FieldLabel"]),
            Paragraph(_escape(r.remediation_template).replace("\n", "<br/>"),
                      styles["FieldValue"]),
        ]
        wrap = Table([[block]], colWidths=[CONTENT_WIDTH])
        wrap.setStyle(TableStyle([
            ("LINEBEFORE", (0, 0), (0, 0), 2, accent),
            ("BACKGROUND", (0, 0), (-1, -1), WHITE),
            ("BOX", (0, 0), (-1, -1), 0.4, SLATE_200),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))
        story.append(KeepTogether(wrap))
        story.append(Spacer(1, 0.15 * inch))

    # Appendix B — Scan metadata
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Appendix B · Scan Metadata", styles["H1"]))
    story.append(HRule(CONTENT_WIDTH, SLATE_200, 0.75))
    story.append(Spacer(1, 0.15 * inch))

    files_scanned: set[str] = {f.evidence.file for f in report.findings}
    when = report.generated_at.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z").strip()
    meta_rows = [
        ["Scan target", str(report.target).replace("\\", "/")],
        ["Generated at", when or report.generated_at.isoformat()],
        ["Report ID", report.id],
        ["Findings", str(len(report.findings))],
        ["Risk score", f"{report.risk_score}/100"],
        ["Files with findings", str(len(files_scanned))],
        ["Scanner version", _scanner_version()],
        ["Engine", "Aegis Static Analyzer · tree-sitter + heuristics"],
    ]
    meta = Table(
        [[Paragraph(f"<b>{k}</b>", styles["TableCell"]),
          Paragraph(f"<font face='Courier' size='8.5'>{_escape(v)}</font>",
                    styles["TableCell"])]
         for k, v in meta_rows],
        colWidths=[1.8 * inch, CONTENT_WIDTH - 1.8 * inch],
    )
    meta.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, SLATE_50]),
        ("BOX", (0, 0), (-1, -1), 0.4, SLATE_200),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, SLATE_200),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(meta)
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph(
        "<para align='center'><font color='#64748B' size='8'>"
        "Generated by Aegis  ·  Powered by IBM Bob"
        "</font></para>",
        styles["BodyMuted"],
    ))
    return story


# ----- Document --------------------------------------------------------------

def _build_doc(out_path: Path) -> BaseDocTemplate:
    doc = BaseDocTemplate(
        str(out_path),
        pagesize=LETTER,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title="HIPAA Technical Safeguards Audit Report",
        author="Aegis",
        subject="HIPAA Technical Safeguards Audit",
    )

    frame_cover = Frame(
        MARGIN, MARGIN, CONTENT_WIDTH, PAGE_HEIGHT - 2 * MARGIN,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="cover",
    )
    frame_body = Frame(
        MARGIN, MARGIN, CONTENT_WIDTH, PAGE_HEIGHT - 2 * MARGIN,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        id="body",
    )
    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[frame_cover],
                     onPage=_draw_cover_background),
        PageTemplate(id="Body", frames=[frame_body],
                     onPage=_draw_body_chrome),
    ])
    return doc


def render(report: Report, out_path: Path) -> Path:
    """Render `report` to a PDF at `out_path`. Returns the output path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    styles = _build_styles()
    doc = _build_doc(out_path)

    story: list = []
    # Cover
    story.extend(_cover_story(report, styles))
    story.append(PageBreak())
    # Switch to body template for everything after
    from reportlab.platypus import NextPageTemplate

    story.insert(0, NextPageTemplate("Cover"))
    # After cover page break, switch to body
    # Replace the bare PageBreak with NextPageTemplate+PageBreak
    story[-1] = NextPageTemplate("Body")
    story.append(PageBreak())

    # Executive summary
    story.extend(_exec_summary_story(report, styles))
    story.append(PageBreak())

    # Findings index
    story.extend(_index_story(report, styles))
    story.append(PageBreak())

    # Per-finding detail
    detail = _findings_detail_story(report, styles)
    if detail:
        story.extend(detail)
        story.append(PageBreak())

    # Appendix
    story.extend(_appendix_story(report, styles))

    doc.build(story)
    return out_path


__all__ = ["render"]
