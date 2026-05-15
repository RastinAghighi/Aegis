"""Run an end-to-end audit: scan the demo, emit a JSON report.

Convenience wrapper around the CLI for the demo flow.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "demo" / "patient-portal"
OUT = ROOT / ".aegis" / "report.json"


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)

    print(f"[..] scanning {TARGET}")
    rc = subprocess.run([sys.executable, "-m", "aegis.cli", "scan", str(TARGET)]).returncode
    if rc != 0:
        return rc

    print(f"[..] writing report to {OUT}")
    rc = subprocess.run(
        [sys.executable, "-m", "aegis.cli", "report", "--format", "json", "--out", str(OUT)]
    ).returncode
    return rc


if __name__ == "__main__":
    sys.exit(main())
