"""Smoke tests for the CLI."""

from click.testing import CliRunner

from aegis.cli import main


def test_cli_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "scan" in result.output
    assert "report" in result.output
    assert "serve-mcp" in result.output


def test_scan_not_implemented(tmp_path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["scan", str(tmp_path)])
    assert result.exit_code == 0
    assert "not implemented" in result.output


def test_report_not_implemented(tmp_path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["report", "--format", "json", "--out", str(tmp_path / "r.json")])
    assert result.exit_code == 0
    assert "not implemented" in result.output


def test_serve_mcp_not_implemented() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["serve-mcp"])
    assert result.exit_code == 0
    assert "not implemented" in result.output
