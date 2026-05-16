"""tree-sitter glue for JavaScript / TypeScript parsing."""

from __future__ import annotations

import re
from typing import Any

try:
    from tree_sitter import Language, Parser
    from tree_sitter_javascript import language as js_language
    
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    Language = None  # type: ignore
    Parser = None  # type: ignore


def get_parser() -> Any:
    """Get a tree-sitter parser for JavaScript/TypeScript."""
    if not TREE_SITTER_AVAILABLE:
        raise RuntimeError(
            "tree-sitter not available. Install with: pip install tree-sitter tree-sitter-javascript"
        )
    
    parser = Parser(Language(js_language()))
    return parser


def parse_js(source_code: str) -> Any:
    """Parse JavaScript/TypeScript source code and return AST root."""
    parser = get_parser()
    tree = parser.parse(bytes(source_code, "utf8"))
    return tree.root_node


def node_to_line_range(node: Any) -> tuple[int, int]:
    """Convert tree-sitter node to 1-indexed line range (inclusive).
    
    Args:
        node: tree-sitter Node object
        
    Returns:
        Tuple of (start_line, end_line) in 1-indexed format
    """
    # tree-sitter uses 0-indexed lines, we need 1-indexed
    return (node.start_point[0] + 1, node.end_point[0] + 1)


def get_node_text(node: Any, source_code: str) -> str:
    """Extract text content of a node."""
    return source_code[node.start_byte : node.end_byte]


def find_route_handlers(tree: Any, source_code: str) -> list[dict[str, Any]]:
    """Find Express route handler definitions.
    
    Returns list of dicts with:
    - method: HTTP method (get, post, put, delete, etc.)
    - path: route path string
    - handler_node: tree-sitter node for the handler function
    - middleware: list of middleware function names
    - line_start: 1-indexed start line
    - line_end: 1-indexed end line
    """
    routes = []
    
    def visit(node: Any) -> None:
        # Look for router.METHOD(path, ...handlers) patterns
        if node.type == "call_expression":
            callee = node.child_by_field_name("function")
            if callee and callee.type == "member_expression":
                obj = callee.child_by_field_name("object")
                prop = callee.child_by_field_name("property")
                
                if obj and prop:
                    obj_text = get_node_text(obj, source_code)
                    method = get_node_text(prop, source_code)
                    
                    # Check if it's a router method call
                    if obj_text == "router" and method in [
                        "get", "post", "put", "delete", "patch", "all", "use"
                    ]:
                        args = node.child_by_field_name("arguments")
                        if args and args.named_child_count >= 2:
                            # First arg is the path
                            path_node = args.named_child(0)
                            path = get_node_text(path_node, source_code).strip('"\'')
                            
                            # Collect middleware names
                            middleware = []
                            for i in range(1, args.named_child_count):
                                arg = args.named_child(i)
                                if arg.type == "identifier":
                                    middleware.append(get_node_text(arg, source_code))
                            
                            line_start, line_end = node_to_line_range(node)
                            routes.append({
                                "method": method,
                                "path": path,
                                "handler_node": node,
                                "middleware": middleware,
                                "line_start": line_start,
                                "line_end": line_end,
                            })
        
        for child in node.children:
            visit(child)
    
    visit(tree)
    return routes


def find_function_calls(tree: Any, source_code: str, name_pattern: str) -> list[dict[str, Any]]:
    """Find function calls matching a regex pattern.
    
    Returns list of dicts with:
    - name: function name
    - node: tree-sitter node
    - line_start: 1-indexed start line
    - line_end: 1-indexed end line
    - text: full call expression text
    """
    pattern = re.compile(name_pattern)
    calls = []
    
    def visit(node: Any) -> None:
        if node.type == "call_expression":
            callee = node.child_by_field_name("function")
            if callee:
                name = get_node_text(callee, source_code)
                if pattern.search(name):
                    line_start, line_end = node_to_line_range(node)
                    calls.append({
                        "name": name,
                        "node": node,
                        "line_start": line_start,
                        "line_end": line_end,
                        "text": get_node_text(node, source_code),
                    })
        
        for child in node.children:
            visit(child)
    
    visit(tree)
    return calls


def find_member_assignments(tree: Any, source_code: str, target_pattern: str) -> list[dict[str, Any]]:
    """Find member assignments like obj.prop = value matching a pattern.
    
    Returns list of dicts with:
    - target: left-hand side (e.g., "patient.ssn")
    - value: right-hand side text
    - node: tree-sitter node
    - line_start: 1-indexed start line
    - line_end: 1-indexed end line
    """
    pattern = re.compile(target_pattern)
    assignments = []
    
    def visit(node: Any) -> None:
        if node.type == "assignment_expression":
            left = node.child_by_field_name("left")
            right = node.child_by_field_name("right")
            
            if left and right and left.type == "member_expression":
                target = get_node_text(left, source_code)
                if pattern.search(target):
                    line_start, line_end = node_to_line_range(node)
                    assignments.append({
                        "target": target,
                        "value": get_node_text(right, source_code),
                        "node": node,
                        "line_start": line_start,
                        "line_end": line_end,
                    })
        
        for child in node.children:
            visit(child)
    
    visit(tree)
    return assignments


def find_object_literals(tree: Any, source_code: str, key_pattern: str) -> list[dict[str, Any]]:
    """Find object literal properties matching a key pattern.
    
    Returns list of dicts with:
    - key: property key
    - value: property value text
    - node: tree-sitter node for the pair
    - line_start: 1-indexed start line
    - line_end: 1-indexed end line
    """
    pattern = re.compile(key_pattern)
    properties = []
    
    def visit(node: Any) -> None:
        if node.type == "pair":
            key_node = node.child_by_field_name("key")
            value_node = node.child_by_field_name("value")
            
            if key_node and value_node:
                key = get_node_text(key_node, source_code).strip('"\'')
                if pattern.search(key):
                    line_start, line_end = node_to_line_range(node)
                    properties.append({
                        "key": key,
                        "value": get_node_text(value_node, source_code),
                        "node": node,
                        "line_start": line_start,
                        "line_end": line_end,
                    })
        
        for child in node.children:
            visit(child)
    
    visit(tree)
    return properties


def find_binary_expressions(tree: Any, source_code: str, pattern: str) -> list[dict[str, Any]]:
    """Find binary expressions (comparisons, logical ops) matching a pattern.
    
    Returns list of dicts with:
    - operator: the operator (===, &&, ||, etc.)
    - left: left operand text
    - right: right operand text
    - node: tree-sitter node
    - line_start: 1-indexed start line
    - line_end: 1-indexed end line
    - text: full expression text
    """
    regex = re.compile(pattern)
    expressions = []
    
    def visit(node: Any) -> None:
        if node.type == "binary_expression":
            text = get_node_text(node, source_code)
            if regex.search(text):
                left = node.child_by_field_name("left")
                right = node.child_by_field_name("right")
                operator_node = node.child(1)  # operator is typically the middle child
                
                line_start, line_end = node_to_line_range(node)
                expressions.append({
                    "operator": get_node_text(operator_node, source_code) if operator_node else "",
                    "left": get_node_text(left, source_code) if left else "",
                    "right": get_node_text(right, source_code) if right else "",
                    "node": node,
                    "line_start": line_start,
                    "line_end": line_end,
                    "text": text,
                })
        
        for child in node.children:
            visit(child)
    
    visit(tree)
    return expressions


def find_sequelize_model_fields(tree: Any, source_code: str) -> list[dict[str, Any]]:
    """Find Sequelize model field definitions.
    
    Returns list of dicts with:
    - field_name: name of the field
    - type: DataTypes.STRING, etc.
    - node: tree-sitter node
    - line_start: 1-indexed start line
    - line_end: 1-indexed end line
    """
    fields = []
    
    def visit(node: Any) -> None:
        # Look for sequelize.define('ModelName', { fields... })
        if node.type == "call_expression":
            callee = node.child_by_field_name("function")
            if callee and callee.type == "member_expression":
                prop = callee.child_by_field_name("property")
                if prop and get_node_text(prop, source_code) == "define":
                    args = node.child_by_field_name("arguments")
                    if args and args.named_child_count >= 2:
                        # Second argument is the fields object
                        fields_obj = args.named_child(1)
                        if fields_obj.type == "object":
                            for pair in fields_obj.children:
                                if pair.type == "pair":
                                    key = pair.child_by_field_name("key")
                                    value = pair.child_by_field_name("value")
                                    if key and value:
                                        field_name = get_node_text(key, source_code).strip('"\'')
                                        line_start, line_end = node_to_line_range(pair)
                                        
                                        # Extract type if it's an object with type property
                                        field_type = ""
                                        if value.type == "object":
                                            for prop in value.children:
                                                if prop.type == "pair":
                                                    prop_key = prop.child_by_field_name("key")
                                                    prop_val = prop.child_by_field_name("value")
                                                    if prop_key and get_node_text(prop_key, source_code).strip('"\'') == "type":
                                                        field_type = get_node_text(prop_val, source_code) if prop_val else ""
                                        
                                        fields.append({
                                            "field_name": field_name,
                                            "type": field_type,
                                            "node": pair,
                                            "line_start": line_start,
                                            "line_end": line_end,
                                        })
        
        for child in node.children:
            visit(child)
    
    visit(tree)
    return fields


__all__ = [
    "get_parser",
    "parse_js",
    "node_to_line_range",
    "get_node_text",
    "find_route_handlers",
    "find_function_calls",
    "find_member_assignments",
    "find_object_literals",
    "find_binary_expressions",
    "find_sequelize_model_fields",
]

# Made with Bob
