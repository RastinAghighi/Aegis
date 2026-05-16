"""Test script to verify the scanner works without full installation."""

import sys
from pathlib import Path

# Add Aegis to path
sys.path.insert(0, str(Path(__file__).parent))

from Aegis.models import Report
from Aegis.rules import ALL_RULES
from Aegis.scanner.base import scan_repository


def main():
    """Run a test scan on the demo patient-portal."""
    print("=" * 80)
    print("AEGIS HIPAA Scanner Test")
    print("=" * 80)
    print()
    
    # Scan the demo patient-portal
    target = Path("demo/patient-portal")
    
    if not target.exists():
        print(f"Error: Target directory not found: {target}")
        return 1
    
    print(f"Scanning: {target}")
    print(f"Rules loaded: {len(ALL_RULES)}")
    print()
    
    try:
        # Run the scan
        findings = scan_repository(target, ALL_RULES)
        
        # Create report
        report = Report(
            target=str(target),
            findings=findings,
        )
        
        print(f"Scan complete!")
        print(f"Total findings: {len(findings)}")
        print()
        
        # Print summary by severity
        print("Findings by Severity:")
        for severity, count in report.counts_by_severity.items():
            if count > 0:
                print(f"  {severity}: {count}")
        print()
        
        print(f"Risk Score: {report.risk_score}/100")
        print()
        
        # Print findings by rule
        findings_by_rule = {}
        for finding in findings:
            rule_id = finding.rule_id
            if rule_id not in findings_by_rule:
                findings_by_rule[rule_id] = []
            findings_by_rule[rule_id].append(finding)
        
        print("Findings by Rule:")
        for rule_id, rule_findings in sorted(findings_by_rule.items()):
            print(f"\n{rule_id}: {rule_findings[0].rule_title} ({len(rule_findings)} findings)")
            for finding in rule_findings:
                print(f"  - {finding.evidence.file}:{finding.evidence.line_start}")
                print(f"    {finding.evidence.why}")
        
        print()
        print("=" * 80)
        
        # Verify expected findings
        ac1_count = len(findings_by_rule.get("AC-1", []))
        en1_count = len(findings_by_rule.get("EN-1", []))
        
        print("\nVerification:")
        print(f"  AC-1 findings: {ac1_count} (expected: 1)")
        print(f"  EN-1 findings: {en1_count} (expected: 2)")
        
        if ac1_count >= 1 and en1_count >= 2:
            print("\n✓ Test PASSED - Expected violations detected!")
            return 0
        else:
            print("\n✗ Test FAILED - Expected violations not detected")
            return 1
            
    except Exception as e:
        print(f"Error during scan: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
