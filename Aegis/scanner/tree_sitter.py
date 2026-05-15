"""tree-sitter glue for JavaScript / TypeScript parsing.

TODO (Bob):
  - load tree_sitter_javascript language and build a Parser
  - provide query helpers used by rules:
      * route_handlers(tree) -> [{ method, path, handler_node, middleware_chain }]
      * function_calls(tree, name_regex) -> [Node]
      * member_assignments(tree, target_regex) -> [Node]
      * object_literals(tree, key_regex) -> [{ key, value, node }]
  - convert tree-sitter Node ranges into 1-indexed line numbers for Evidence
"""

from __future__ import annotations

# Intentionally minimal. Bob fills this in.
