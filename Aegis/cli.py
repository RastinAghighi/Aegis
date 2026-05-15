"""Aegis CLI — three commands: scan, report, serve-mcp."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.group(help="Aegis — HIPAA compliance code auditor.")
@click.version_option(package_name="aegis")
def main() -> None:
    """Top-level CLI group."""


@main.command(help="Scan a codebase for HIPAA violations.")
@click.argument(
    "target",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--rules",
    "rule_ids",
    multiple=True,
    help="Subset of rule IDs to run (e.g. -r AC-1 -r EN-1). Default: all.",
)
@click.option(
    "--severity",
    type=click.Choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"], case_sensitive=False),
    help="Only emit findings at this severity or higher.",
)
def scan(target: Path, rule_ids: tuple[str, ...], severity: str | None) -> None:
    """Scan TARGET for HIPAA violations and persist findings to .aegis/findings.db."""
    click.echo(f"[aegis] scan: not implemented (target={target}, rules={rule_ids or 'all'}, severity={severity or 'any'})")
    sys.exit(0)


@main.command(help="Generate a report from the latest scan results.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["pdf", "json"], case_sensitive=False),
    default="pdf",
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(dir_okay=False, path_type=Path),
    required=True,
    help="Output file path.",
)
def report(fmt: str, out_path: Path) -> None:
    """Render findings as PDF or JSON."""
    click.echo(f"[aegis] report: not implemented (format={fmt}, out={out_path})")
    sys.exit(0)


@main.command("serve-mcp", help="Start the Aegis MCP server (Bob connects here).")
@click.option("--port", type=int, default=8765, show_default=True, help="MCP port.")
def serve_mcp(port: int) -> None:
    """Launch the MCP server over stdio (port reserved for future TCP transport)."""
    click.echo(f"[aegis] serve-mcp: not implemented (port={port})")
    sys.exit(0)


if __name__ == "__main__":
    main()
