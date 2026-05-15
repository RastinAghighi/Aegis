"""Seed the demo Patient Portal database from demo/patient-portal/seed.sql.

Assumes `docker compose up -d patient-portal-db` is already running on
localhost:5432 with the default dev credentials from .env.example.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED_SQL = ROOT / "demo" / "patient-portal" / "seed.sql"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--container",
        default="aegis-patient-portal-db",
        help="Postgres container name (default: aegis-patient-portal-db)",
    )
    p.add_argument(
        "--db", default="patient_portal", help="database name (default: patient_portal)"
    )
    p.add_argument("--user", default="aegis", help="db user (default: aegis)")
    args = p.parse_args()

    if not SEED_SQL.exists():
        print(f"[fail] seed file not found: {SEED_SQL}", file=sys.stderr)
        return 1

    docker = shutil.which("docker")
    if not docker:
        print("[fail] docker not on PATH", file=sys.stderr)
        return 1

    cmd = [
        docker,
        "exec",
        "-i",
        args.container,
        "psql",
        "-U",
        args.user,
        "-d",
        args.db,
    ]
    print(f"[..] seeding {args.db} via {args.container}")
    with SEED_SQL.open("rb") as fh:
        proc = subprocess.run(cmd, stdin=fh, env=os.environ.copy())
    if proc.returncode != 0:
        print("[fail] seed failed", file=sys.stderr)
        return proc.returncode
    print("[ok] demo data seeded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
