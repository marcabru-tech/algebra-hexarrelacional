"""
tests/test_codegen.py — Tests for core/codegen.py (Python → JS / Rust transpilation).

Each test class focuses on a language target and verifies that the emitted
output contains the expected tokens / structure for common Python constructs.
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.codegen import py_to_js, py_to_rust


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lines(code: str) -> list:
    return [ln.strip() for ln in code.splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# JavaScript transpilation
# ---------------------------------------------------------------------------

class TestPyToJS:
    def test_simple_function(self) -> None:
        src = "def add(a, b):\n    return a + b"
        out = py_to_js(src)
        assert "function add(a, b)" in out
        assert "return" in out

    def test_async_function(self) -> None:
        src = "async def fetch(url):\n    return url"
        out = py_to_js(src)
        assert "async function fetch(url)" in out

    def test_class(self) -> None:
        src = "class Dog:\n    def bark(self):\n        return 1"
        out = py_to_js(src)
        assert "class Dog" in out
        assert "function bark(self)" in out

    def test_if_else(self) -> None:
        src = "if x > 0:\n    y = 1\nelse:\n    y = 0"
        out = py_to_js(src)
        assert "if (" in out
        assert "} else {" in out

    def test_elif(self) -> None:
        src = "if x > 0:\n    y = 1\nelif x < 0:\n    y = -1\nelse:\n    y = 0"
        out = py_to_js(src)
        assert "} else if (" in out

    def test_for_range_one_arg(self) -> None:
        src = "for i in range(10):\n    pass"
        out = py_to_js(src)
        assert "for (let i = 0; i < 10; i++)" in out

    def test_for_range_two_args(self) -> None:
        src = "for i in range(3, 7):\n    pass"
        out = py_to_js(src)
        assert "for (let i = 3; i < 7; i++)" in out

    def test_for_range_three_args(self) -> None:
        src = "for i in range(0, 10, 2):\n    pass"
        out = py_to_js(src)
        assert "i += 2" in out

    def test_for_generic(self) -> None:
        src = "for item in items:\n    pass"
        out = py_to_js(src)
        assert "for (const item of items)" in out

    def test_while_loop(self) -> None:
        src = "while True:\n    break"
        out = py_to_js(src)
        assert "while (true)" in out
        assert "break;" in out

    def test_assignment(self) -> None:
        src = "x = 42"
        out = py_to_js(src)
        assert "let x = 42;" in out

    def test_string_constant(self) -> None:
        src = 'msg = "hello"'
        out = py_to_js(src)
        assert '"hello"' in out

    def test_boolean_constant(self) -> None:
        src = "flag = True"
        out = py_to_js(src)
        assert "true" in out

    def test_none_constant(self) -> None:
        src = "x = None"
        out = py_to_js(src)
        assert "null" in out

    def test_binary_op(self) -> None:
        src = "z = a + b"
        out = py_to_js(src)
        assert "(a + b)" in out

    def test_comparison(self) -> None:
        src = "if a == b:\n    pass"
        out = py_to_js(src)
        assert "===" in out

    def test_function_call(self) -> None:
        src = "result = foo(x, y)"
        out = py_to_js(src)
        assert "foo(x, y)" in out

    def test_attribute_access(self) -> None:
        src = "n = obj.name"
        out = py_to_js(src)
        assert "obj.name" in out

    def test_list_literal(self) -> None:
        src = "xs = [1, 2, 3]"
        out = py_to_js(src)
        assert "[1, 2, 3]" in out

    def test_dict_literal(self) -> None:
        src = 'd = {"k": 1}'
        out = py_to_js(src)
        assert '"k": 1' in out

    def test_return_none(self) -> None:
        src = "def f():\n    return"
        out = py_to_js(src)
        assert "return undefined;" in out

    def test_invalid_python_raises(self) -> None:
        with pytest.raises(SyntaxError):
            py_to_js("def (:")

    def test_output_is_string(self) -> None:
        assert isinstance(py_to_js("x = 1"), str)

    def test_nested_function(self) -> None:
        src = "def outer(x):\n    def inner(y):\n        return y\n    return inner(x)"
        out = py_to_js(src)
        assert "function outer(x)" in out
        assert "function inner(y)" in out

    def test_continue_break(self) -> None:
        src = "for i in range(5):\n    if i == 3:\n        continue\n    if i == 4:\n        break"
        out = py_to_js(src)
        assert "continue;" in out
        assert "break;" in out


# ---------------------------------------------------------------------------
# Rust transpilation
# ---------------------------------------------------------------------------

class TestPyToRust:
    def test_simple_function(self) -> None:
        src = "def greet(name):\n    return name"
        out = py_to_rust(src)
        assert "fn greet(name: &str)" in out
        assert "return" in out

    def test_async_function(self) -> None:
        src = "async def load(path):\n    return path"
        out = py_to_rust(src)
        assert "async fn load(path: &str)" in out

    def test_class_becomes_struct_impl(self) -> None:
        src = "class Cat:\n    def meow(self):\n        return 1"
        out = py_to_rust(src)
        assert "struct Cat" in out
        assert "impl Cat" in out
        assert "fn meow(self: &str)" in out

    def test_if_else(self) -> None:
        src = "if x > 0:\n    y = 1\nelse:\n    y = 0"
        out = py_to_rust(src)
        assert "if " in out
        assert "} else {" in out

    def test_elif(self) -> None:
        src = "if x > 0:\n    y = 1\nelif x < 0:\n    y = -1\nelse:\n    y = 0"
        out = py_to_rust(src)
        assert "} else if " in out

    def test_for_range_one_arg(self) -> None:
        src = "for i in range(10):\n    pass"
        out = py_to_rust(src)
        assert "for i in 0..10" in out

    def test_for_range_two_args(self) -> None:
        src = "for i in range(3, 7):\n    pass"
        out = py_to_rust(src)
        assert "for i in 3..7" in out

    def test_for_range_three_args(self) -> None:
        src = "for i in range(0, 10, 2):\n    pass"
        out = py_to_rust(src)
        assert "step_by" in out

    def test_for_generic(self) -> None:
        src = "for item in items:\n    pass"
        out = py_to_rust(src)
        assert "for item in items.iter()" in out

    def test_while_loop(self) -> None:
        src = "while True:\n    break"
        out = py_to_rust(src)
        assert "while true" in out
        assert "break;" in out

    def test_assignment(self) -> None:
        src = "x = 42"
        out = py_to_rust(src)
        assert "let x = 42;" in out

    def test_boolean_constants(self) -> None:
        src = "a = True\nb = False"
        out = py_to_rust(src)
        assert "true" in out
        assert "false" in out

    def test_none_maps_to_unit(self) -> None:
        src = "x = None"
        out = py_to_rust(src)
        assert "()" in out

    def test_comparison_uses_double_eq(self) -> None:
        src = "if a == b:\n    pass"
        out = py_to_rust(src)
        assert "==" in out
        assert "===" not in out

    def test_list_literal(self) -> None:
        src = "xs = [1, 2, 3]"
        out = py_to_rust(src)
        assert "vec![1, 2, 3]" in out

    def test_invalid_python_raises(self) -> None:
        with pytest.raises(SyntaxError):
            py_to_rust("def (:")

    def test_output_is_string(self) -> None:
        assert isinstance(py_to_rust("x = 1"), str)
