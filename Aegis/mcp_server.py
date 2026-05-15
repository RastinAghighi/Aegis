"""MCP server entrypoint.

TODO (Bob): expose Aegis tools over MCP so an LLM agent can:
  - list_findings(severity?, rule_id?)
  - get_finding(finding_id) -> full evidence + CFR
  - explain_rule(rule_id) -> CFR text and remediation guidance
  - run_scan(path) -> scan a target directory and persist findings
  - generate_report(format, path) -> emit PDF/JSON report

Implementation uses the `mcp` Python SDK (stdio transport for local Bob).
"""
