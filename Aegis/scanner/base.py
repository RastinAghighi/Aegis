"""Scanner base classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .tree_sitter import parse_js


@dataclass
class SourceFile:
    """A single file under scan."""

    path: Path
    language: str  # "javascript" | "typescript" | "sql" | "json" | ...
    text: str
    # tree-sitter AST root; populated lazily by the parser. Untyped to avoid
    # importing tree_sitter at module import time.
    tree: Any | None = field(default=None)


class Scanner:
    """Walks a target directory, classifies files, and parses them."""

    # Directories to skip during scan
    SKIP_DIRS = {
        "node_modules",
        ".git",
        "dist",
        "build",
        ".venv",
        "__pycache__",
        ".next",
        ".nuxt",
        "coverage",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
    }

    # File extensions to language mapping
    LANGUAGE_MAP = {
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".sql": "sql",
        ".json": "json",
        ".py": "python",
    }

    def __init__(self, target: Path) -> None:
        self.target = target

    def walk(self) -> Iterable[SourceFile]:
        """Walk the target directory and yield SourceFile objects for scannable files."""
        if not self.target.exists():
            raise FileNotFoundError(f"Target path does not exist: {self.target}")

        if self.target.is_file():
            # Single file scan
            yield from self._process_file(self.target)
        else:
            # Directory scan
            yield from self._walk_directory(self.target)

    def _walk_directory(self, directory: Path) -> Iterable[SourceFile]:
        """Recursively walk a directory, skipping excluded paths."""
        try:
            for item in directory.iterdir():
                # Skip hidden files and excluded directories
                if item.name.startswith(".") and item.name not in {".env", ".env.example"}:
                    continue

                if item.is_dir():
                    if item.name not in self.SKIP_DIRS:
                        yield from self._walk_directory(item)
                elif item.is_file():
                    yield from self._process_file(item)
        except PermissionError:
            # Skip directories we can't read
            pass

    def _process_file(self, file_path: Path) -> Iterable[SourceFile]:
        """Process a single file and yield a SourceFile if it's scannable."""
        ext = file_path.suffix.lower()
        language = self.LANGUAGE_MAP.get(ext)

        if language:
            try:
                text = file_path.read_text(encoding="utf-8")
                source_file = SourceFile(
                    path=file_path,
                    language=language,
                    text=text,
                    tree=None,
                )
                yield source_file
            except (UnicodeDecodeError, PermissionError):
                # Skip files we can't read
                pass

    def parse(self, src: SourceFile) -> SourceFile:
        """Parse a SourceFile and populate its tree field.
        
        Currently only supports JavaScript/TypeScript via tree-sitter.
        """
        if src.language in ("javascript", "typescript") and src.tree is None:
            try:
                src.tree = parse_js(src.text)
            except Exception as e:
                print(f"Parse failed for {src.path}: {type(e).__name__}: {e}")
        return src


def scan_repository(
    target_path: Path,
    rules: list[Any],
) -> list[Any]:
    """Scan a repository with the given rules and return all findings.
    
    Args:
        target_path: Path to scan (file or directory)
        rules: List of Rule instances to apply
        
    Returns:
        List of Finding objects
    """
    scanner = Scanner(target_path)
    all_findings = []

    # Collect all source files first for context
    source_files = list(scanner.walk())
    
    # Build context dict with file paths for cross-file analysis
    context = {
        "all_files": [str(sf.path) for sf in source_files],
        "source_files": source_files,
    }

    for source_file in source_files:
        # Parse the file if it's JavaScript/TypeScript
        if source_file.language in ("javascript", "typescript"):
            scanner.parse(source_file)

            # Apply each rule
            for rule in rules:
                if hasattr(rule, "match_js") and source_file.tree:
                    try:
                        findings = rule.match_js(
                            source_file.tree,
                            str(source_file.path),
                            context,
                        )
                        all_findings.extend(findings)
                    except Exception as e:
                        # Log error but continue scanning
                        print(f"Error applying rule {rule.rule_id} to {source_file.path}: {e}")

    return all_findings


__all__ = ["SourceFile", "Scanner", "scan_repository"]

# Made with Bob
