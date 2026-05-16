"""MCP server exposing Aegis HIPAA scanner tools."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .models import Finding, Report
from .rules import ALL_RULES
from .scanner.base import scan_repository


# Initialize MCP server
app = Server("aegis-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return [
        Tool(
            name="list_rules",
            description="List all HIPAA Technical Safeguards rules available for scanning",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="scan_file",
            description="Scan a single file for HIPAA violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to scan",
                    },
                },
                "required": ["file_path"],
            },
        ),
        Tool(
            name="scan_repo",
            description="Scan an entire repository for HIPAA violations",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Path to the repository to scan",
                    },
                },
                "required": ["repo_path"],
            },
        ),
        Tool(
            name="get_rule",
            description="Get detailed information about a specific rule",
            inputSchema={
                "type": "object",
                "properties": {
                    "rule_id": {
                        "type": "string",
                        "description": "Rule ID (e.g., 'AC-1', 'EN-1')",
                    },
                },
                "required": ["rule_id"],
            },
        ),
        Tool(
            name="get_remediation_template",
            description="Get remediation guidance for a specific rule",
            inputSchema={
                "type": "object",
                "properties": {
                    "rule_id": {
                        "type": "string",
                        "description": "Rule ID (e.g., 'AC-1', 'EN-1')",
                    },
                },
                "required": ["rule_id"],
            },
        ),
        Tool(
            name="generate_evidence",
            description="Generate evidence artifact for a violation",
            inputSchema={
                "type": "object",
                "properties": {
                    "violation_id": {
                        "type": "string",
                        "description": "Finding/violation ID",
                    },
                    "findings_json": {
                        "type": "string",
                        "description": "JSON string of findings from previous scan",
                    },
                },
                "required": ["violation_id", "findings_json"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "list_rules":
        return await handle_list_rules()
    elif name == "scan_file":
        return await handle_scan_file(arguments["file_path"])
    elif name == "scan_repo":
        return await handle_scan_repo(arguments["repo_path"])
    elif name == "get_rule":
        return await handle_get_rule(arguments["rule_id"])
    elif name == "get_remediation_template":
        return await handle_get_remediation_template(arguments["rule_id"])
    elif name == "generate_evidence":
        return await handle_generate_evidence(
            arguments["violation_id"],
            arguments["findings_json"]
        )
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def handle_list_rules() -> list[TextContent]:
    """List all available rules."""
    rules_data = []
    for rule in ALL_RULES:
        rules_data.append({
            "rule_id": rule.rule_id,
            "cfr": rule.cfr,
            "title": rule.title,
            "severity": rule.severity.value,
            "description": rule.description,
        })
    
    return [TextContent(
        type="text",
        text=json.dumps(rules_data, indent=2)
    )]


async def handle_scan_file(file_path: str) -> list[TextContent]:
    """Scan a single file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return [TextContent(
                type="text",
                text=f"Error: File not found: {file_path}"
            )]
        
        findings = scan_repository(path, ALL_RULES)
        findings_data = [f.model_dump(mode="json") for f in findings]
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "file": file_path,
                "findings_count": len(findings),
                "findings": findings_data,
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error scanning file: {str(e)}"
        )]


async def handle_scan_repo(repo_path: str) -> list[TextContent]:
    """Scan an entire repository."""
    try:
        path = Path(repo_path)
        if not path.exists():
            return [TextContent(
                type="text",
                text=f"Error: Repository not found: {repo_path}"
            )]
        
        findings = scan_repository(path, ALL_RULES)
        
        # Create report
        report = Report(
            target=repo_path,
            findings=findings,
        )
        
        report_data = report.model_dump(mode="json")
        report_data["risk_score"] = report.risk_score
        report_data["counts_by_severity"] = report.counts_by_severity
        
        return [TextContent(
            type="text",
            text=json.dumps(report_data, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error scanning repository: {str(e)}"
        )]


async def handle_get_rule(rule_id: str) -> list[TextContent]:
    """Get detailed rule information."""
    rule = None
    for r in ALL_RULES:
        if r.rule_id == rule_id:
            rule = r
            break
    
    if not rule:
        return [TextContent(
            type="text",
            text=f"Error: Rule not found: {rule_id}"
        )]
    
    rule_data = {
        "rule_id": rule.rule_id,
        "cfr": rule.cfr,
        "title": rule.title,
        "description": rule.description,
        "severity": rule.severity.value,
        "remediation_template": rule.remediation_template,
    }
    
    return [TextContent(
        type="text",
        text=json.dumps(rule_data, indent=2)
    )]


async def handle_get_remediation_template(rule_id: str) -> list[TextContent]:
    """Get remediation template for a rule."""
    rule = None
    for r in ALL_RULES:
        if r.rule_id == rule_id:
            rule = r
            break
    
    if not rule:
        return [TextContent(
            type="text",
            text=f"Error: Rule not found: {rule_id}"
        )]
    
    template_data = {
        "rule_id": rule.rule_id,
        "code_template": rule.remediation_template,
        "cfr_citation": f"45 CFR § {rule.cfr}",
        "explanation": rule.description,
    }
    
    return [TextContent(
        type="text",
        text=json.dumps(template_data, indent=2)
    )]


async def handle_generate_evidence(
    violation_id: str,
    findings_json: str
) -> list[TextContent]:
    """Generate evidence artifact for a violation."""
    try:
        findings_data = json.loads(findings_json)
        
        # Find the specific finding
        finding_data = None
        if isinstance(findings_data, list):
            for f in findings_data:
                if f.get("id") == violation_id:
                    finding_data = f
                    break
        elif isinstance(findings_data, dict):
            if findings_data.get("id") == violation_id:
                finding_data = findings_data
        
        if not finding_data:
            return [TextContent(
                type="text",
                text=f"Error: Violation not found: {violation_id}"
            )]
        
        evidence = finding_data.get("evidence", {})
        
        # Build evidence artifact
        artifact = {
            "violation_id": violation_id,
            "rule_id": finding_data.get("rule_id"),
            "file": evidence.get("file"),
            "location": {
                "line_start": evidence.get("line_start"),
                "line_end": evidence.get("line_end"),
            },
            "code_snippet": evidence.get("snippet"),
            "explanation": evidence.get("why"),
            "cfr_reference": finding_data.get("cfr", {}).get("section"),
            "severity": finding_data.get("severity"),
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(artifact, indent=2)
        )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error generating evidence: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run():
    """Entry point for the MCP server."""
    asyncio.run(main())


if __name__ == "__main__":
    run()

# Made with Bob
