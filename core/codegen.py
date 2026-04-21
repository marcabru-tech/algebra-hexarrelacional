"""
core/codegen.py — AST-based Python → JavaScript / Rust transpilation.

Provides two public functions:

    py_to_js(source: str) -> str
        Transpile a Python source string to JavaScript.

    py_to_rust(source: str) -> str
        Transpile a Python source string to Rust.

Supported Python constructs:
    - FunctionDef / AsyncFunctionDef
    - ClassDef (→ JS class / Rust struct + impl)
    - If / elif / else
    - For with range() → idiomatic counted loops; generic For → for-of / .iter()
    - While
    - Return, Assign, AugAssign, AnnAssign
    - Expr (expression statements)
    - Pass, Break, Continue
    - Expressions: Constant, Name, BinOp, UnaryOp, BoolOp, Compare,
                   Call, Attribute, Subscript, List, Tuple, Dict

Unsupported nodes are emitted as a comment placeholder so that the output
is always syntactically present (though may be semantically incomplete).
"""

from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Shared operator maps
# ---------------------------------------------------------------------------

_BIN_OPS: Dict[str, str] = {
    "Add": "+", "Sub": "-", "Mult": "*", "Div": "/",
    "Mod": "%", "Pow": "**", "FloorDiv": "//",
    "BitAnd": "&", "BitOr": "|", "BitXor": "^",
    "LShift": "<<", "RShift": ">>",
}

_UNARY_OPS: Dict[str, str] = {
    "USub": "-", "UAdd": "+", "Not": "!", "Invert": "~",
}

_JS_CMP_OPS: Dict[str, str] = {
    "Eq": "===", "NotEq": "!==",
    "Lt": "<", "LtE": "<=", "Gt": ">", "GtE": ">=",
    "Is": "===", "IsNot": "!==",
    "In": "in", "NotIn": "not in",
}

_RS_CMP_OPS: Dict[str, str] = {
    "Eq": "==", "NotEq": "!=",
    "Lt": "<", "LtE": "<=", "Gt": ">", "GtE": ">=",
    "Is": "==", "IsNot": "!=",
    "In": "in", "NotIn": "not in",
}


# ---------------------------------------------------------------------------
# JavaScript visitor
# ---------------------------------------------------------------------------

class _PyToJSVisitor(ast.NodeVisitor):
    """Walk a Python AST and emit JavaScript source lines."""

    def __init__(self) -> None:
        self._lines: List[str] = []
        self._indent: int = 0

    # ------------------------------------------------------------------
    # helpers

    def _emit(self, line: str) -> None:
        self._lines.append("    " * self._indent + line)

    def _block(self, body: list) -> None:
        self._indent += 1
        for stmt in body:
            self.visit(stmt)
        self._indent -= 1

    # ------------------------------------------------------------------
    # statement visitors

    def visit_Module(self, node: ast.Module) -> None:
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        args = ", ".join(arg.arg for arg in node.args.args)
        self._emit(f"function {node.name}({args}) {{")
        self._block(node.body)
        self._emit("}")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        args = ", ".join(arg.arg for arg in node.args.args)
        self._emit(f"async function {node.name}({args}) {{")
        self._block(node.body)
        self._emit("}")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._emit(f"class {node.name} {{")
        self._block(node.body)
        self._emit("}")

    def visit_Return(self, node: ast.Return) -> None:
        val = self._expr(node.value) if node.value else "undefined"
        self._emit(f"return {val};")

    def visit_Assign(self, node: ast.Assign) -> None:
        targets = ", ".join(self._expr(t) for t in node.targets)
        value = self._expr(node.value)
        self._emit(f"let {targets} = {value};")

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        target = self._expr(node.target)
        op = _BIN_OPS.get(type(node.op).__name__, "?")
        value = self._expr(node.value)
        self._emit(f"{target} {op}= {value};")

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value:
            target = self._expr(node.target)
            value = self._expr(node.value)
            self._emit(f"let {target} = {value};")

    def visit_If(self, node: ast.If) -> None:
        self._emit(f"if ({self._expr(node.test)}) {{")
        self._block(node.body)
        orelse = node.orelse
        while orelse:
            if len(orelse) == 1 and isinstance(orelse[0], ast.If):
                elif_node = orelse[0]
                self._emit(f"}} else if ({self._expr(elif_node.test)}) {{")
                self._block(elif_node.body)
                orelse = elif_node.orelse
            else:
                self._emit("} else {")
                self._block(orelse)
                orelse = []
        self._emit("}")

    def visit_For(self, node: ast.For) -> None:
        if (
            isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range"
        ):
            var = self._expr(node.target)
            args = node.iter.args
            if len(args) == 1:
                stop = self._expr(args[0])
                self._emit(f"for (let {var} = 0; {var} < {stop}; {var}++) {{")
            elif len(args) == 2:
                start, stop = self._expr(args[0]), self._expr(args[1])
                self._emit(f"for (let {var} = {start}; {var} < {stop}; {var}++) {{")
            else:
                start = self._expr(args[0])
                stop = self._expr(args[1])
                step = self._expr(args[2])
                self._emit(
                    f"for (let {var} = {start}; {var} < {stop}; {var} += {step}) {{"
                )
        else:
            var = self._expr(node.target)
            iterable = self._expr(node.iter)
            self._emit(f"for (const {var} of {iterable}) {{")
        self._block(node.body)
        self._emit("}")

    def visit_While(self, node: ast.While) -> None:
        self._emit(f"while ({self._expr(node.test)}) {{")
        self._block(node.body)
        self._emit("}")

    def visit_Expr(self, node: ast.Expr) -> None:
        self._emit(self._expr(node.value) + ";")

    def visit_Pass(self, node: ast.Pass) -> None:
        self._emit("// pass")

    def visit_Break(self, node: ast.Break) -> None:
        self._emit("break;")

    def visit_Continue(self, node: ast.Continue) -> None:
        self._emit("continue;")

    def generic_visit(self, node: ast.AST) -> None:
        self._emit(f"/* unsupported: {type(node).__name__} */")

    # ------------------------------------------------------------------
    # expression helper

    def _expr(self, node: Any) -> str:  # noqa: ANN401
        if node is None:
            return "null"
        if isinstance(node, ast.Constant):
            if node.value is None:
                return "null"
            if node.value is True:
                return "true"
            if node.value is False:
                return "false"
            if isinstance(node.value, str):
                escaped = node.value.replace("\\", "\\\\").replace('"', '\\"')
                return f'"{escaped}"'
            return str(node.value)
        if isinstance(node, ast.Name):
            name_map = {"None": "null", "True": "true", "False": "false"}
            return name_map.get(node.id, node.id)
        if isinstance(node, ast.BinOp):
            op = _BIN_OPS.get(type(node.op).__name__, "?")
            return f"({self._expr(node.left)} {op} {self._expr(node.right)})"
        if isinstance(node, ast.UnaryOp):
            op = _UNARY_OPS.get(type(node.op).__name__, "?")
            return f"({op}{self._expr(node.operand)})"
        if isinstance(node, ast.BoolOp):
            op = "&&" if isinstance(node.op, ast.And) else "||"
            return f" {op} ".join(f"({self._expr(v)})" for v in node.values)
        if isinstance(node, ast.Compare):
            parts = [self._expr(node.left)]
            for cmp_op, comp in zip(node.ops, node.comparators):
                parts.append(_JS_CMP_OPS.get(type(cmp_op).__name__, "?"))
                parts.append(self._expr(comp))
            return " ".join(parts)
        if isinstance(node, ast.Call):
            func = self._expr(node.func)
            args = ", ".join(self._expr(a) for a in node.args)
            return f"{func}({args})"
        if isinstance(node, ast.Attribute):
            return f"{self._expr(node.value)}.{node.attr}"
        if isinstance(node, ast.Subscript):
            return f"{self._expr(node.value)}[{self._expr(node.slice)}]"
        if isinstance(node, ast.List):
            elts = ", ".join(self._expr(e) for e in node.elts)
            return f"[{elts}]"
        if isinstance(node, ast.Tuple):
            elts = ", ".join(self._expr(e) for e in node.elts)
            return f"[{elts}]"
        if isinstance(node, ast.Dict):
            pairs = ", ".join(
                f"{self._expr(k)}: {self._expr(v)}"
                for k, v in zip(node.keys, node.values)
            )
            return "{" + pairs + "}"
        return f"/* expr:{type(node).__name__} */"


# ---------------------------------------------------------------------------
# Rust visitor
# ---------------------------------------------------------------------------

class _PyToRustVisitor(ast.NodeVisitor):
    """Walk a Python AST and emit Rust source lines."""

    def __init__(self) -> None:
        self._lines: List[str] = []
        self._indent: int = 0

    # ------------------------------------------------------------------
    # helpers

    def _emit(self, line: str) -> None:
        self._lines.append("    " * self._indent + line)

    def _block(self, body: list) -> None:
        self._indent += 1
        for stmt in body:
            self.visit(stmt)
        self._indent -= 1

    # ------------------------------------------------------------------
    # statement visitors

    def visit_Module(self, node: ast.Module) -> None:
        for stmt in node.body:
            self.visit(stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        args = ", ".join(f"{arg.arg}: &str" for arg in node.args.args)
        self._emit(f"fn {node.name}({args}) {{")
        self._block(node.body)
        self._emit("}")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        args = ", ".join(f"{arg.arg}: &str" for arg in node.args.args)
        self._emit(f"async fn {node.name}({args}) {{")
        self._block(node.body)
        self._emit("}")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._emit(f"struct {node.name} {{")
        self._emit("}")
        self._emit(f"impl {node.name} {{")
        self._block(node.body)
        self._emit("}")

    def visit_Return(self, node: ast.Return) -> None:
        val = self._expr(node.value) if node.value else "()"
        self._emit(f"return {val};")

    def visit_Assign(self, node: ast.Assign) -> None:
        targets = ", ".join(self._expr(t) for t in node.targets)
        value = self._expr(node.value)
        self._emit(f"let {targets} = {value};")

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        target = self._expr(node.target)
        op = _BIN_OPS.get(type(node.op).__name__, "?")
        value = self._expr(node.value)
        self._emit(f"{target} {op}= {value};")

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value:
            target = self._expr(node.target)
            ann = self._expr(node.annotation)
            value = self._expr(node.value)
            self._emit(f"let {target}: {ann} = {value};")

    def visit_If(self, node: ast.If) -> None:
        self._emit(f"if {self._expr(node.test)} {{")
        self._block(node.body)
        orelse = node.orelse
        while orelse:
            if len(orelse) == 1 and isinstance(orelse[0], ast.If):
                elif_node = orelse[0]
                self._emit(f"}} else if {self._expr(elif_node.test)} {{")
                self._block(elif_node.body)
                orelse = elif_node.orelse
            else:
                self._emit("} else {")
                self._block(orelse)
                orelse = []
        self._emit("}")

    def visit_For(self, node: ast.For) -> None:
        if (
            isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range"
        ):
            var = self._expr(node.target)
            args = node.iter.args
            if len(args) == 1:
                stop = self._expr(args[0])
                self._emit(f"for {var} in 0..{stop} {{")
            elif len(args) == 2:
                start, stop = self._expr(args[0]), self._expr(args[1])
                self._emit(f"for {var} in {start}..{stop} {{")
            else:
                start = self._expr(args[0])
                stop = self._expr(args[1])
                step = self._expr(args[2])
                self._emit(
                    f"for {var} in ({start}..{stop}).step_by({step} as usize) {{"
                )
        else:
            var = self._expr(node.target)
            iterable = self._expr(node.iter)
            self._emit(f"for {var} in {iterable}.iter() {{")
        self._block(node.body)
        self._emit("}")

    def visit_While(self, node: ast.While) -> None:
        self._emit(f"while {self._expr(node.test)} {{")
        self._block(node.body)
        self._emit("}")

    def visit_Expr(self, node: ast.Expr) -> None:
        self._emit(self._expr(node.value) + ";")

    def visit_Pass(self, node: ast.Pass) -> None:
        self._emit("// pass")

    def visit_Break(self, node: ast.Break) -> None:
        self._emit("break;")

    def visit_Continue(self, node: ast.Continue) -> None:
        self._emit("continue;")

    def generic_visit(self, node: ast.AST) -> None:
        self._emit(f"/* unsupported: {type(node).__name__} */")

    # ------------------------------------------------------------------
    # expression helper

    def _expr(self, node: Any) -> str:  # noqa: ANN401
        if node is None:
            return "()"
        if isinstance(node, ast.Constant):
            if node.value is None:
                return "()"
            if node.value is True:
                return "true"
            if node.value is False:
                return "false"
            if isinstance(node.value, str):
                escaped = node.value.replace("\\", "\\\\").replace('"', '\\"')
                return f'"{escaped}"'
            return str(node.value)
        if isinstance(node, ast.Name):
            name_map = {"None": "()", "True": "true", "False": "false"}
            return name_map.get(node.id, node.id)
        if isinstance(node, ast.BinOp):
            op = _BIN_OPS.get(type(node.op).__name__, "?")
            return f"({self._expr(node.left)} {op} {self._expr(node.right)})"
        if isinstance(node, ast.UnaryOp):
            op = _UNARY_OPS.get(type(node.op).__name__, "?")
            return f"({op}{self._expr(node.operand)})"
        if isinstance(node, ast.BoolOp):
            op = "&&" if isinstance(node.op, ast.And) else "||"
            return f" {op} ".join(f"({self._expr(v)})" for v in node.values)
        if isinstance(node, ast.Compare):
            parts = [self._expr(node.left)]
            for cmp_op, comp in zip(node.ops, node.comparators):
                parts.append(_RS_CMP_OPS.get(type(cmp_op).__name__, "?"))
                parts.append(self._expr(comp))
            return " ".join(parts)
        if isinstance(node, ast.Call):
            func = self._expr(node.func)
            args = ", ".join(self._expr(a) for a in node.args)
            return f"{func}({args})"
        if isinstance(node, ast.Attribute):
            return f"{self._expr(node.value)}.{node.attr}"
        if isinstance(node, ast.Subscript):
            return f"{self._expr(node.value)}[{self._expr(node.slice)}]"
        if isinstance(node, ast.List):
            elts = ", ".join(self._expr(e) for e in node.elts)
            return f"vec![{elts}]"
        if isinstance(node, ast.Tuple):
            elts = ", ".join(self._expr(e) for e in node.elts)
            return f"({elts},)"
        if isinstance(node, ast.Dict):
            pairs = "".join(
                f'\n        map.insert({self._expr(k)}, {self._expr(v)});'
                for k, v in zip(node.keys, node.values)
            )
            return (
                "{\n        let mut map = std::collections::HashMap::new();"
                + pairs
                + "\n        map\n    }"
            )
        return f"/* expr:{type(node).__name__} */"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def py_to_js(source: str) -> str:
    """Transpile Python *source* to JavaScript.

    Parses *source* as a Python module and converts each top-level
    statement to its JavaScript equivalent.  Unsupported constructs are
    emitted as ``/* unsupported: <NodeType> */`` comments so the output
    is always well-formed text.

    Args:
        source: Valid Python source code as a string.

    Returns:
        JavaScript source code string.

    Raises:
        SyntaxError: If *source* is not valid Python.
    """
    tree = ast.parse(source)
    visitor = _PyToJSVisitor()
    visitor.visit(tree)
    return "\n".join(visitor._lines)


def py_to_rust(source: str) -> str:
    """Transpile Python *source* to Rust.

    Parses *source* as a Python module and converts each top-level
    statement to its Rust equivalent.  Unsupported constructs are emitted
    as ``/* unsupported: <NodeType> */`` comments so the output is always
    well-formed text.

    Args:
        source: Valid Python source code as a string.

    Returns:
        Rust source code string.

    Raises:
        SyntaxError: If *source* is not valid Python.
    """
    tree = ast.parse(source)
    visitor = _PyToRustVisitor()
    visitor.visit(tree)
    return "\n".join(visitor._lines)
