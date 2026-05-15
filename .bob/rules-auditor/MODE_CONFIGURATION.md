# Auditor Mode Configuration Guide

This guide provides step-by-step instructions for configuring the "Auditor" custom mode in Bob IDE.

## Prerequisites

1. Bob IDE installed and running
2. This repository opened as the active workspace
3. HIPAA Rules Engine MCP server registered (see MCP setup instructions separately)

## Configuration Steps

### Step 1: Open Bob IDE Settings

1. Click the **Bob icon** in the VS Code activity bar (left sidebar)
2. Click the **gear icon** (⚙️) in the Bob sidebar header
3. Select **"Modes"** from the settings menu

### Step 2: Create New Custom Mode

1. In the Modes settings page, click **"+ Add Custom Mode"**
2. You will see a form with multiple fields to configure

### Step 3: Fill in Basic Information

**Field: Slug**
```
auditor
```
- This is the internal identifier for the mode
- Must be lowercase, no spaces
- Used in `.bob/rules-auditor/` directory name

**Field: Name**
```
🛡️ Auditor
```
- Display name shown in the mode selector
- The shield emoji (🛡️) indicates security/compliance focus

**Field: Description**
```
HIPAA compliance auditor mode for healthcare software security assessments. Produces audit-ready findings with CFR citations, evidence excerpts, and remediation templates. Automatically scans repositories on open and generates formal compliance reports.
```

### Step 4: Configure Mode Behavior

**Field: Rule Definition**

Select: **"Use custom rules file"**

Then specify:
```
.bob/rules-auditor/AGENTS.md
```

This tells Bob to load the HIPAA-specific rules we created in the repository.

**Field: When to Use**
```
Use this mode when:
- Conducting HIPAA compliance audits of healthcare software
- Investigating specific security violations in patient data systems
- Generating remediation plans for regulatory findings
- Preparing audit-ready documentation with CFR citations
- Reviewing code changes for HIPAA Security Rule compliance

Do NOT use for:
- General code development (use Code mode)
- Non-healthcare software projects
- Casual code reviews without regulatory requirements
```

### Step 5: Mode-Specific Custom Instructions

**Field: Mode-Specific Custom Instructions**
```
# Auditor Mode Behavior

## Automatic Actions on Repository Open
1. Run baseline scan: `aegis scan .`
2. Generate violation summary by severity and CFR subsection
3. Present findings in formal audit report format

## Response Format Requirements
- Every violation claim MUST cite 45 CFR § 164.312 subsection
- Include full regulatory text, not just section numbers
- Provide file paths and 1-indexed line numbers for all evidence
- Use formal audit language, not casual developer terminology

## Violation Investigation Format
When investigating violations, always provide:
1. **CFR Citation**: Full regulatory reference with exact text
2. **Evidence Excerpt**: Code snippet with file:line context
3. **Remediation Template**: Compliant code with inline CFR comments
4. **Impact Narrative**: Business risk in formal audit language

## Remediation PR Requirements
When generating remediation PRs:
- Add CFR citations as code comments for each change
- Include detailed PR description with regulatory justification
- Show before/after compliance metrics
- Provide testing checklist for compliance verification

## Severity Classification
- **Critical**: Direct PHI exposure, authentication bypass, encryption failures
- **High**: Access control gaps, audit log failures, session management issues
- **Medium**: Incomplete implementations, missing safeguards
- **Low**: Documentation gaps, best practice deviations

## MCP Server Usage
- Use HIPAA Rules Engine MCP for real-time CFR lookups
- Validate all compliance interpretations against current regulations
- Query format: `get_cfr_section("164.312(a)(1)")`
```

### Step 6: Configure Tool Access

**Field: Available Tools**

Enable the following tools:
- ✅ **read_file** - Required for analyzing source code
- ✅ **write_to_file** - Required for generating remediation files
- ✅ **apply_diff** - Required for targeted code fixes
- ✅ **insert_content** - Required for adding compliance comments
- ✅ **execute_command** - Required for running `aegis scan` and other CLI tools
- ✅ **list_files** - Required for repository structure analysis
- ✅ **search_files** - Required for finding violation patterns
- ✅ **list_code_definition_names** - Required for understanding code structure
- ✅ **MCP Tools** - Required for HIPAA Rules Engine access
- ❌ **Browser Tools** - Not needed for code auditing

### Step 7: Set Scope

**Field: Mode Scope**

Select: **"Project-Specific"**

This ensures the Auditor mode configuration is saved in the repository (`.bob/` directory) and version-controlled, so all team members use the same compliance auditing standards.

### Step 8: Save Configuration

1. Click **"Save Mode"** at the bottom of the form
2. Bob will create/update the mode configuration
3. The mode will appear in your mode selector with the 🛡️ icon

## Verification Steps

After saving, verify the configuration:

1. **Check file creation**:
   ```bash
   ls -la .bob/rules-auditor/
   ```
   Should show: `AGENTS.md` and `MODE_CONFIGURATION.md`

2. **Switch to Auditor mode**:
   - Click the mode selector in Bob sidebar
   - Select "🛡️ Auditor"
   - Bob should load the custom rules

3. **Test automatic behavior**:
   - Close and reopen the repository
   - Auditor mode should automatically run baseline scan
   - Should see formal audit report with CFR citations

## MCP Server Registration

The Auditor mode requires the HIPAA Rules Engine MCP server. Register it separately:

1. Open Bob Settings → MCP Servers
2. Click "Add MCP Server"
3. Configure:
   - **Name**: HIPAA Rules Engine
   - **Command**: `aegis serve-mcp`
   - **Transport**: stdio
   - **Auto-start**: Yes

## Troubleshooting

**Mode not appearing in selector**:
- Verify `.bob/rules-auditor/AGENTS.md` exists
- Check Bob logs for parsing errors
- Restart VS Code

**Automatic scan not running**:
- Verify `aegis` CLI is installed: `pip install -e .[dev]`
- Check that `aegis scan` command works manually
- Review mode-specific custom instructions

**MCP tools not available**:
- Verify HIPAA Rules Engine MCP server is registered
- Check MCP server status in Bob Settings
- Restart MCP server if needed

## Usage Examples

### Example 1: Baseline Audit
```
User: "Audit this repository for HIPAA compliance"

Auditor Mode Response:
HIPAA COMPLIANCE AUDIT REPORT
Generated: 2026-05-15 19:34:00 UTC
Repository: Aegis HIPAA Scanner

EXECUTIVE SUMMARY
Total Violations: 5
- Critical: 2
- High: 2
- Medium: 1
- Low: 0

VIOLATIONS BY CFR SUBSECTION
45 CFR § 164.312(a)(1) - Access Control: 2 findings
45 CFR § 164.312(d) - Authentication: 2 findings
45 CFR § 164.312(b) - Audit Controls: 1 finding

[Detailed findings follow with full CFR citations...]
```

### Example 2: Violation Investigation
```
User: "Investigate the access control violation in patients.js"

Auditor Mode Response:
FINDING: AC-1 Violation - Insufficient Access Controls
CFR REFERENCE: 45 CFR § 164.312(a)(1) - "Implement technical policies..."

EVIDENCE:
File: demo/patient-portal/routes/patients.js
Lines: 24-28
[Code excerpt with violation highlighted]

REMEDIATION:
[Compliant code example with CFR comments]

IMPACT: Unrestricted access to PHI constitutes a breach...
```

### Example 3: Remediation PR
```
User: "Generate remediation PR for all Critical violations"

Auditor Mode Response:
[Creates multi-file PR with:]
- CFR-cited code changes
- Detailed regulatory justification
- Before/after compliance metrics
- Testing checklist
```

## Best Practices

1. **Always run baseline scan first** - Understand full compliance posture before investigating specific violations
2. **Cite CFR sections accurately** - Use MCP server to verify regulatory text
3. **Provide complete evidence** - Include sufficient code context (5+ lines)
4. **Test remediations** - Run `aegis scan` after applying fixes to verify compliance
5. **Document intentional violations** - Note demo/test violations to avoid false positives

## Additional Resources

- HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/
- 45 CFR Part 164: https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164
- Aegis Documentation: `docs/HIPAA-RULES.md`