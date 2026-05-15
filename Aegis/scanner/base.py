"""Scanner base classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class SourceFile:
    """A single file under scan."""

    path: Path
    language: str  # "javascript" | "typescript" | "sql" | "json" | ...
    text: str
    # tree-sitter AST root; populated lazily by the parser. Untyped to avoid
    # importing tree_sitter at module import time.
    tree: object | None = field(default=None)


class Scanner:
    """Walks a target directory, classifies files, and parses them.

    TODO (Bob):
      - implement walk(target_path) -> Iterable[SourceFile]
      - implement parse(SourceFile) using tree_sitter when language is JS/TS
      - skip node_modules, .git, dist, build, .venv, __pycache__
    """

    def __init__(self, target: Path) -> None:
        self.target = target

    def walk(self) -> Iterable[SourceFile]:
        raise NotImplementedError

    def parse(self, src: SourceFile) -> SourceFile:
        raise NotImplementedError
