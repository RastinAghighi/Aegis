"""Regex-based pattern matching for non-AST inputs (SQL, .env, plain text).

Used by rules that don't need a full AST (e.g. TR-1 looking for `ssl: false`
in a config file, or AC-3 sniffing for hardcoded admin/admin literals).

TODO (Bob):
  - provide a small Matcher API: Matcher.find(pattern, src) -> [Match]
  - each Match carries line_start/line_end/snippet for Evidence
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Match:
    line_start: int
    line_end: int
    snippet: str
    groups: tuple[str, ...]


def find_all(pattern: str | re.Pattern[str], text: str) -> list[Match]:
    """Find every occurrence of `pattern` in `text`, return Match objects with 1-indexed lines."""
    rx = re.compile(pattern) if isinstance(pattern, str) else pattern
    out: list[Match] = []
    for m in rx.finditer(text):
        start_line = text.count("\n", 0, m.start()) + 1
        end_line = text.count("\n", 0, m.end()) + 1
        snippet = text.splitlines()[start_line - 1] if start_line - 1 < len(text.splitlines()) else m.group(0)
        out.append(Match(start_line, end_line, snippet, m.groups()))
    return out
