"""FastAPI app — exposes findings, rules, and the demo PHI flow graph.

Deployment target: Render free tier. Frontend: Vercel-hosted dashboard.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from ..models import Report
from ..rules import ALL_RULES
from ..scanner.base import scan_repository

logger = logging.getLogger("aegis.api")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _default_repo_root() -> Path:
    # Aegis/api/main.py -> Aegis/api -> Aegis -> repo root
    return Path(__file__).resolve().parent.parent.parent


REPO_ROOT = Path(os.environ.get("AEGIS_REPO_ROOT") or _default_repo_root())
SCAN_TARGET_REL = os.environ.get("AEGIS_SCAN_TARGET", "demo/patient-portal")
SCAN_TARGET = (REPO_ROOT / SCAN_TARGET_REL).resolve()
ALLOWED_ORIGINS_RAW = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
)
RATE_LIMIT_SECONDS = int(os.environ.get("RATE_LIMIT_SECONDS", "60"))


def _split_origins(raw: str) -> tuple[list[str], str | None]:
    """Split CORS origin list into plain origins + a regex covering wildcards.

    Wildcards must take the form ``https://*.example.com``. The ``*`` is
    expanded to ``[^/]+`` so any subdomain (including preview deployments)
    matches.
    """
    plain: list[str] = []
    patterns: list[str] = []
    for item in (s.strip() for s in raw.split(",")):
        if not item:
            continue
        if "*" in item:
            esc = re.escape(item).replace(r"\*", r"[^/]+")
            patterns.append(esc)
        else:
            plain.append(item)
    regex = "|".join(patterns) if patterns else None
    return plain, regex


PLAIN_ORIGINS, ORIGIN_REGEX = _split_origins(ALLOWED_ORIGINS_RAW)


# ---------------------------------------------------------------------------
# Cache + rate limit state
# ---------------------------------------------------------------------------

_scan_lock = threading.Lock()
_cache: dict[str, Any] = {"report": None, "last_scan": None}

_rate_lock = threading.Lock()
_rate_buckets: dict[str, float] = {}


def _run_scan_and_cache() -> Report:
    """Execute a full scan, log the result, and store it in the cache."""
    started = time.perf_counter()
    findings = scan_repository(SCAN_TARGET, ALL_RULES)
    report = Report(target=str(SCAN_TARGET), findings=findings)
    duration_ms = int((time.perf_counter() - started) * 1000)

    with _scan_lock:
        _cache["report"] = report
        _cache["last_scan"] = datetime.now(timezone.utc)

    # Approximate file count without re-walking: use a quick listing.
    try:
        files_scanned = sum(1 for _ in SCAN_TARGET.rglob("*") if _.is_file())
    except OSError:
        files_scanned = -1

    logger.info(
        "scan complete target=%s files=%s findings=%s risk=%s duration_ms=%s",
        SCAN_TARGET,
        files_scanned,
        len(report.findings),
        report.risk_score,
        duration_ms,
    )
    return report


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str) -> float:
    """Return 0 if allowed, otherwise seconds remaining until the next try."""
    now = time.time()
    with _rate_lock:
        last = _rate_buckets.get(ip, 0.0)
        wait = RATE_LIMIT_SECONDS - (now - last)
        if wait > 0:
            return wait
        _rate_buckets[ip] = now
        return 0.0


# ---------------------------------------------------------------------------
# Lifespan: run initial scan on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "startup repo_root=%s scan_target=%s rate_limit_s=%s",
        REPO_ROOT,
        SCAN_TARGET,
        RATE_LIMIT_SECONDS,
    )
    try:
        _run_scan_and_cache()
    except Exception as exc:  # noqa: BLE001
        logger.exception("initial scan failed: %s", exc)
    yield


app = FastAPI(
    title="Aegis API",
    version="0.1.0",
    description="HIPAA compliance code auditor — dashboard backend.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=PLAIN_ORIGINS,
    allow_origin_regex=ORIGIN_REGEX,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health() -> dict[str, Any]:
    report: Report | None = _cache.get("report")
    last_scan: datetime | None = _cache.get("last_scan")
    return {
        "status": "ok",
        "scan_target": str(SCAN_TARGET),
        "last_scan": last_scan.isoformat() if last_scan else None,
        "findings_cached": len(report.findings) if report else 0,
    }


@app.get("/api/findings")
def get_findings() -> dict[str, Any]:
    report: Report | None = _cache.get("report")
    if report is None:
        report = _run_scan_and_cache()
    payload = report.model_dump(mode="json")
    payload["counts_by_severity"] = report.counts_by_severity
    payload["risk_score"] = report.risk_score
    return payload


@app.get("/api/findings/{finding_id}")
def get_finding(finding_id: str) -> dict[str, Any]:
    report: Report | None = _cache.get("report")
    if report is None:
        report = _run_scan_and_cache()
    for finding in report.findings:
        if finding.id == finding_id:
            return finding.model_dump(mode="json")
    raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found")


@app.get("/api/rules")
def get_rules() -> list[dict[str, str]]:
    return [
        {
            "rule_id": r.rule_id,
            "title": r.title,
            "cfr_section": r.cfr,
            "severity": r.severity.value,
            "description": r.description,
        }
        for r in ALL_RULES
    ]


@app.post("/api/scan")
def post_scan(request: Request) -> dict[str, Any]:
    ip = _client_ip(request)
    wait = _check_rate_limit(ip)
    if wait > 0:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Rate limit: one scan per {RATE_LIMIT_SECONDS}s per IP. "
                f"Try again in {int(wait) + 1}s."
            ),
        )
    report = _run_scan_and_cache()
    payload = report.model_dump(mode="json")
    payload["counts_by_severity"] = report.counts_by_severity
    payload["risk_score"] = report.risk_score
    return payload


@app.get("/api/flow-graph")
def get_flow_graph() -> dict[str, Any]:
    return {
        "title": "Cross-File PHI Leak Through Error Handler",
        "cfr_citation": "45 CFR § 164.312(b)",
        "severity": "CRITICAL",
        "description": (
            "PHI flow that per-file scanning cannot catch — "
            "requires cross-module reasoning"
        ),
        "nodes": [
            {
                "id": "patient-model",
                "label": "Patient.js",
                "sublabel": "Defines SSN field",
                "file": "demo/patient-portal/models/Patient.js",
                "line": 22,
                "type": "schema",
            },
            {
                "id": "patient-route",
                "label": "GET /patients/:id",
                "sublabel": "Queries Patient.findByPk()",
                "file": "demo/patient-portal/routes/patients.js",
                "line": 24,
                "type": "route",
            },
            {
                "id": "error-handler",
                "label": "Global error handler",
                "sublabel": "console.error(err) logs full object",
                "file": "demo/patient-portal/server.js",
                "line": 31,
                "type": "error_handler",
            },
            {
                "id": "logs",
                "label": "Application logs",
                "sublabel": "Anyone with log access reads PHI",
                "file": None,
                "line": None,
                "type": "sink",
            },
        ],
        "edges": [
            {"from": "patient-model", "to": "patient-route", "label": "queried via findByPk"},
            {"from": "patient-route", "to": "error-handler", "label": "error includes patient context"},
            {"from": "error-handler", "to": "logs", "label": "PHI written to stdout"},
        ],
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("Aegis.api.main:app", host="0.0.0.0", port=port, reload=False)
