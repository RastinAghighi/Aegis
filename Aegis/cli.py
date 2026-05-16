"""Aegis CLI — scan, report, scan-and-report, serve-mcp."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .models import Finding, Report, Severity
from .reporter import pdf as pdf_reporter
from .rules import ALL_RULES
from .scanner.base import scan_repository

SEVERITY_RANK = {
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3,
}


def _select_rules(rule_ids: tuple[str, ...]) -> list:
    if not rule_ids:
        return ALL_RULES
    wanted = {rid.upper() for rid in rule_ids}
    selected = [r for r in ALL_RULES if r.rule_id.upper() in wanted]
    missing = wanted - {r.rule_id.upper() for r in ALL_RULES}
    if missing:
        click.echo(f"[aegis] warning: unknown rule ids: {', '.join(sorted(missing))}",
                   err=True)
    return selected or ALL_RULES


def _filter_by_severity(findings: list[Finding], threshold: str | None) -> list[Finding]:
    if not threshold:
        return findings
    try:
        thr = Severity(threshold.upper())
    except ValueError:
        return findings
    cutoff = SEVERITY_RANK[thr]
    return [f for f in findings if SEVERITY_RANK[f.severity] >= cutoff]


def _run_scan(target: Path, rule_ids: tuple[str, ...], severity: str | None) -> Report:
    rules = _select_rules(rule_ids)
    findings = scan_repository(target, rules)
    findings = _filter_by_severity(findings, severity)
    return Report(target=str(target), findings=findings)


def _write_report_json(report: Report, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump(mode="json")
    payload["counts_by_severity"] = report.counts_by_severity
    payload["risk_score"] = report.risk_score
    out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _load_report_json(in_path: Path) -> Report:
    data = json.loads(in_path.read_text(encoding="utf-8"))
    # Strip computed-only fields so Pydantic doesn't choke.
    for key in ("counts_by_severity", "risk_score"):
        data.pop(key, None)
    return Report.model_validate(data)


@click.group(help="Aegis — HIPAA compliance code auditor.")
@click.version_option(package_name="aegis")
def main() -> None:
    """Top-level CLI group."""


@main.command(help="Scan a codebase for HIPAA violations and write findings JSON.")
@click.argument(
    "target",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path),
)
@click.option(
    "--output", "-o",
    "out_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("findings.json"),
    show_default=True,
    help="Path to write findings JSON.",
)
@click.option(
    "--rules", "-r",
    "rule_ids",
    multiple=True,
    help="Subset of rule IDs to run (e.g. -r AC-1 -r EN-1). Default: all.",
)
@click.option(
    "--severity",
    type=click.Choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"], case_sensitive=False),
    help="Only emit findings at this severity or higher.",
)
def scan(target: Path, out_path: Path, rule_ids: tuple[str, ...],
         severity: str | None) -> None:
    """Scan TARGET for HIPAA violations and write a findings JSON file."""
    click.echo(f"[aegis] scanning {target} ...")
    report = _run_scan(target, rule_ids, severity)
    _write_report_json(report, out_path)
    counts = report.counts_by_severity
    click.echo(
        f"[aegis] {len(report.findings)} findings "
        f"(C:{counts['CRITICAL']} H:{counts['HIGH']} "
        f"M:{counts['MEDIUM']} L:{counts['LOW']}) · "
        f"risk score {report.risk_score}/100"
    )
    click.echo(f"[aegis] wrote {out_path}")


@main.command(help="Generate a PDF report from a findings JSON file.")
@click.option(
    "--input", "-i",
    "in_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to findings JSON produced by `aegis scan`.",
)
@click.option(
    "--output", "-o",
    "out_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("audit-report.pdf"),
    show_default=True,
    help="Path to write the PDF report.",
)
def report(in_path: Path, out_path: Path) -> None:
    """Render a findings JSON file as a PDF audit report."""
    click.echo(f"[aegis] reading findings from {in_path}")
    rep = _load_report_json(in_path)
    click.echo(f"[aegis] rendering PDF -> {out_path}")
    pdf_reporter.render(rep, out_path)
    click.echo(f"[aegis] wrote {out_path}")


@main.command("scan-and-report", help="Scan a codebase and write the PDF in one call.")
@click.argument(
    "target",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, path_type=Path),
)
@click.option(
    "--output", "-o",
    "out_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("audit-report.pdf"),
    show_default=True,
    help="Path to write the PDF report.",
)
@click.option(
    "--findings-json",
    "findings_json",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Optional path to also persist findings as JSON.",
)
@click.option(
    "--rules", "-r",
    "rule_ids",
    multiple=True,
    help="Subset of rule IDs to run (default: all).",
)
@click.option(
    "--severity",
    type=click.Choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"], case_sensitive=False),
    help="Only emit findings at this severity or higher.",
)
def scan_and_report(target: Path, out_path: Path,
                    findings_json: Path | None,
                    rule_ids: tuple[str, ...],
                    severity: str | None) -> None:
    """Run a scan and produce the PDF report in a single invocation."""
    click.echo(f"[aegis] scanning {target} ...")
    rep = _run_scan(target, rule_ids, severity)
    counts = rep.counts_by_severity
    click.echo(
        f"[aegis] {len(rep.findings)} findings "
        f"(C:{counts['CRITICAL']} H:{counts['HIGH']} "
        f"M:{counts['MEDIUM']} L:{counts['LOW']}) · "
        f"risk score {rep.risk_score}/100"
    )
    if findings_json:
        _write_report_json(rep, findings_json)
        click.echo(f"[aegis] wrote findings JSON {findings_json}")
    click.echo(f"[aegis] rendering PDF -> {out_path}")
    pdf_reporter.render(rep, out_path)
    click.echo(f"[aegis] wrote {out_path}")


@main.command("serve-mcp", help="Start the Aegis MCP server (Bob connects here).")
@click.option("--port", type=int, default=8765, show_default=True,
              help="Reserved for future TCP transport — current transport is stdio.")
def serve_mcp(port: int) -> None:
    """Launch the Aegis MCP server over stdio."""
    from . import mcp_server

    click.echo(f"[aegis] serve-mcp starting (port hint={port}, transport=stdio)",
               err=True)
    mcp_server.run()


if __name__ == "__main__":
    main()
