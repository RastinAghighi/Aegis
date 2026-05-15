"""SQLAlchemy + SQLite persistence for findings.

Database file lives at `.aegis/findings.db` relative to the project root.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _db_path() -> Path:
    root = Path.cwd() / ".aegis"
    root.mkdir(parents=True, exist_ok=True)
    return root / "findings.db"


def _engine_url() -> str:
    return f"sqlite:///{_db_path().as_posix()}"


class Base(DeclarativeBase):
    pass


class FindingRow(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True)
    rule_id = Column(String, index=True, nullable=False)
    rule_title = Column(String, nullable=False)
    severity = Column(String, index=True, nullable=False)
    file = Column(String, index=True, nullable=False)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    snippet = Column(Text, nullable=False)
    why = Column(Text, nullable=False)
    cfr = Column(JSON, nullable=False)
    remediation = Column(Text, nullable=False)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())


class ReportRow(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True)
    target = Column(String, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    finding_ids = Column(JSON, nullable=False, default=list)


_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(_engine_url(), future=True)
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SessionLocal()


def init_db() -> None:
    """Create tables if they don't exist."""
    Base.metadata.create_all(get_engine())


# TODO (Bob): add helpers — insert_finding(), list_findings(filters), latest_report()
