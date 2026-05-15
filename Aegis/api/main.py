"""FastAPI app — exposes findings and reports to the dashboard."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Aegis API",
    version="0.1.0",
    description="HIPAA compliance code auditor — dashboard backend.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# TODO (Bob): implement endpoints
#   GET /findings?severity=&rule_id=
#   GET /findings/{id}
#   GET /reports
#   GET /reports/{id}
#   POST /scan { target: "..." }
