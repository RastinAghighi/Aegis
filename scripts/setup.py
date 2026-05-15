"""Aegis local setup script.

Verifies host toolchain (Python 3.11+, Node 20+, Docker), installs the Python
package in editable mode, and installs dashboard dependencies. Designed to run
cleanly on Windows PowerShell, macOS, and Linux.

Usage:
    python scripts/setup.py            # full setup
    python scripts/setup.py --check    # just verify toolchain
    python scripts/setup.py --no-dash  # skip dashboard install
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class SetupError(RuntimeError):
    pass


def _run(cmd: list[str], cwd: Path | None = None) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        shell=False,
    )
    if proc.returncode != 0:
        raise SetupError(
            f"Command failed: {' '.join(cmd)}\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )
    return (proc.stdout or "").strip()


def _which(name: str) -> str | None:
    return shutil.which(name)


def check_python() -> None:
    if sys.version_info < (3, 11):
        raise SetupError(
            f"Python 3.11+ required, found {sys.version_info.major}.{sys.version_info.minor}"
        )
    print(f"[ok] python {sys.version.split()[0]}")


def check_node() -> None:
    node = _which("node")
    if not node:
        raise SetupError("Node.js not found on PATH. Install Node 20+ from https://nodejs.org")
    out = _run([node, "--version"])  # "v20.11.1"
    m = re.match(r"v(\d+)\.", out)
    if not m or int(m.group(1)) < 20:
        raise SetupError(f"Node 20+ required, found {out}")
    print(f"[ok] node {out}")


def check_docker() -> None:
    docker = _which("docker")
    if not docker:
        print("[warn] docker not found — `docker compose up` will fail. Install Docker Desktop.")
        return
    try:
        out = _run([docker, "--version"])
        print(f"[ok] {out}")
    except SetupError as e:
        print(f"[warn] docker present but `docker --version` failed: {e}")


def install_python_package() -> None:
    print("[..] installing aegis (editable) + dev extras")
    _run([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
    print("[ok] aegis installed in editable mode")


def install_dashboard() -> None:
    npm = _which("npm")
    if not npm:
        raise SetupError("npm not found on PATH")
    dash = ROOT / "dashboard"
    if not (dash / "package.json").exists():
        print("[skip] dashboard/package.json missing")
        return
    print("[..] installing dashboard dependencies (this may take a minute)")
    _run([npm, "install"], cwd=dash)
    print("[ok] dashboard deps installed")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true", help="only verify toolchain")
    p.add_argument("--no-dash", action="store_true", help="skip dashboard install")
    args = p.parse_args()

    try:
        check_python()
        check_node()
        check_docker()
        if args.check:
            return 0
        install_python_package()
        if not args.no_dash:
            install_dashboard()
    except SetupError as e:
        print(f"[fail] {e}", file=sys.stderr)
        return 1

    print()
    print("Setup complete. Next steps:")
    print("  docker compose up -d")
    print("  curl http://localhost:3000/health")
    print("  aegis --help")
    print("  cd dashboard && npm run dev")
    return 0


if __name__ == "__main__":
    sys.exit(main())
