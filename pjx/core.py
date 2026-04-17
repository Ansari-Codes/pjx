"""
PJx core module — the engine that accumulates and emits JavaScript code.

Design principles
-----------------
1.  Every construct (Let, If, While, …) appends lines to a **global buffer**
    so the user never has to manage state manually.
2.  `VarProxy` objects overload Python operators so that expressions like
    `x > 10` or `y + 1` produce **JavaScript expression strings** rather than
    Python booleans / ints.
3.  Context managers (`with If(…):`, `with While(…):`, …) handle indentation
    automatically.
4.  `JavaScript.save_this_file()` dumps the accumulated buffer to disk.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Optional

# Sentinel value used to distinguish "no value provided" from explicit None/null
_UNSET = object()


# ---------------------------------------------------------------------------
# Global code accumulator
# ---------------------------------------------------------------------------

class _CodeBuffer:
    """Singleton-like buffer that holds the generated JavaScript lines."""

    def __init__(self) -> None:
        self._lines: list[str] = []
        self._indent_level: int = 0
        self._indent_str: str = "    "  # 4 spaces

    # -- internal helpers ---------------------------------------------------

    def _indent(self) -> str:
        return self._indent_str * self._indent_level

    def add(self, line: str) -> None:
        """Append *line* at the current indentation level."""
        stripped = line.strip()
        if stripped == "":
            self._lines.append("")
        else:
            self._lines.append(f"{self._indent()}{stripped}")

    def add_blank(self) -> None:
        """Append a blank line (no indentation)."""
        self._lines.append("")

    @contextmanager
    def indent_block(self):
        """Context manager that increases indentation for the duration of the block."""
        self._indent_level += 1
        try:
            yield
        finally:
            self._indent_level -= 1

    def output(self) -> str:
        """Return the full accumulated JavaScript as a single string."""
        # Collapse multiple consecutive blank lines into one
        result_lines: list[str] = []
        prev_blank = False
        for line in self._lines:
            if line.strip() == "":
                if not prev_blank:
                    result_lines.append("")
                prev_blank = True
            else:
                result_lines.append(line)
                prev_blank = False
        return "\n".join(result_lines) + "\n"

    def reset(self) -> None:
        """Clear the buffer (useful for testing or starting fresh)."""
        self._lines.clear()
        self._indent_level = 0


# Module-level singleton
_buf = _CodeBuffer()


# ---------------------------------------------------------------------------
# Pending-close mechanism for If/Elif/Else/Switch/Case chains
# ---------------------------------------------------------------------------

_pending_close: bool = False


def _flush_pending_close() -> None:
    """If there's a pending close brace from an if/elif/else chain, emit it."""
    global _pending_close
    if _pending_close:
        _buf.add("}")
        _pending_close = False


# ---------------------------------------------------------------------------
# JavaScript expression helpers
# ---------------------------------------------------------------------------

def _js_repr(value: Any) -> str:
    """Convert a Python value to its JavaScript literal representation."""
    if isinstance(value, VarProxy):
        return value._name
    if isinstance(value, _JSExpr):
        return value.expr
    if isinstance(value, Await):
        return value.expr
    if isinstance(value, Spread):
        return value._js()
    if isinstance(value, _DestructExpr):
        return value._js()
    if isinstance(value, Obj):
        return value._js()
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return _convert_template_string(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if value is None:
        return "null"
    if isinstance(value, list):
        items = ", ".join(_js_repr(item) for item in value)
        return f"[{items}]"
    if isinstance(value, dict):
        pairs = ", ".join(
            f"{k}: {_js_repr(v)}" for k, v in value.items()
        )
        return f"{{{pairs}}}"
    return str(value)


class _JSExpr:
    """Wrapper for a raw JavaScript expression string (used internally)."""

    def __init__(self, expr: str) -> None:
        self.expr = expr

    def __repr__(self) -> str:
        return f"_JSExpr({self.expr!r})"


def _as_expr(value: Any) -> str:
    """Turn a Python value into a JS expression string."""
    if isinstance(value, VarProxy):
        return value._name
    if isinstance(value, _JSExpr):
        return value.expr
    if isinstance(value, Await):
        return value.expr
    if isinstance(value, Spread):
        return value._js()
    if isinstance(value, _DestructExpr):
        return value._js()
    if isinstance(value, Obj):
        return value._js()
    return _js_repr(value)


def _as_expr_raw(value: Any) -> str:
    """Turn a Python value into a raw JS fragment — strings are NOT quoted."""
    if isinstance(value, VarProxy):
        return value._name
    if isinstance(value, _JSExpr):
        return value.expr
    if isinstance(value, Await):
        return value.expr
    if isinstance(value, Spread):
        return value._js()
    if isinstance(value, _DestructExpr):
        return value._js()
    if isinstance(value, Obj):
        return value._js()
    if isinstance(value, str):
        # Raw JS — emit as-is, no quoting
        return value
    return _js_repr(value)


def JS(expr: str) -> _JSExpr:
    """
    Create a raw JavaScript expression from a string.

    Use this when you need to pass an identifier or expression that
    should **not** be quoted as a string literal.

    Example::

        Return(JS("name"))       # -> return name;
        Return(JS("a + b"))      # -> return a + b;
        FnCall("console.log", JS("x"))  # -> console.log(x);
    """
    return _JSExpr(expr)


def _convert_template_string(text: str) -> str:
    """
    Convert a Python string containing ``${var}`` interpolation markers
    into a JavaScript template literal wrapped in backticks.

    If the string contains ``${…}`` it becomes a template literal.
    Otherwise it stays as a regular double-quoted string.
    """
    if "${" in text:
        # Escape any backticks that might be in the original string
        escaped = text.replace("`", "\\`")
        return f"`{escaped}`"
    # Regular string — use double quotes, escape internal quotes
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


# ---------------------------------------------------------------------------
# VarProxy — the smart variable wrapper
# ---------------------------------------------------------------------------

class VarProxy:
    """
    A proxy object that represents a JavaScript variable.

    When used in Python expressions (e.g. ``x > 10``) it returns a
    ``_JSExpr`` that captures the JavaScript equivalent of that expression.

    Supports: arithmetic (+, -, *, /, //, %, **),
    comparisons (==, !=, <, <=, >, >=),
    bitwise (&, |, ^, <<, >>),
    logical (and, or — mapped to &&, ||),
    unary (-, ~, not — mapped to !).

    The ``.set(value)`` method emits an assignment statement.
    """

    def __init__(self, name: str) -> None:
        self._name = name

    # -- assignment ---------------------------------------------------------

    def set(self, value: Any) -> "VarProxy":
        """Emit ``<name> = <value>;`` and return self for chaining."""
        _flush_pending_close()
        _buf.add(f"{self._name} = {_as_expr(value)};")
        return self

    # -- arithmetic operators -----------------------------------------------

    def __add__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} + {_as_expr(other)}")

    def __radd__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{_as_expr(other)} + {self._name}")

    def __sub__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} - {_as_expr(other)}")

    def __rsub__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{_as_expr(other)} - {self._name}")

    def __mul__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} * {_as_expr(other)}")

    def __rmul__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{_as_expr(other)} * {self._name}")

    def __truediv__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} / {_as_expr(other)}")

    def __rtruediv__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{_as_expr(other)} / {self._name}")

    def __floordiv__(self, other: Any) -> _JSExpr:
        # JS has no //, approximate with Math.floor
        return _JSExpr(f"Math.floor({self._name} / {_as_expr(other)})")

    def __mod__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} % {_as_expr(other)}")

    def __pow__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"Math.pow({self._name}, {_as_expr(other)})")

    # -- comparison operators -----------------------------------------------

    def __eq__(self, other: Any) -> _JSExpr:  # type: ignore[override]
        return _JSExpr(f"{self._name} === {_as_expr(other)}")

    def __ne__(self, other: Any) -> _JSExpr:  # type: ignore[override]
        return _JSExpr(f"{self._name} !== {_as_expr(other)}")

    def __lt__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} < {_as_expr(other)}")

    def __le__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} <= {_as_expr(other)}")

    def __gt__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} > {_as_expr(other)}")

    def __ge__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} >= {_as_expr(other)}")

    # -- bitwise operators --------------------------------------------------

    def __and__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} & {_as_expr(other)}")

    def __or__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} | {_as_expr(other)}")

    def __xor__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} ^ {_as_expr(other)}")

    def __lshift__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} << {_as_expr(other)}")

    def __rshift__(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self._name} >> {_as_expr(other)}")

    def __invert__(self) -> _JSExpr:
        return _JSExpr(f"~{self._name}")

    # -- unary operators ----------------------------------------------------

    def __neg__(self) -> _JSExpr:
        return _JSExpr(f"-{self._name}")

    def __pos__(self) -> _JSExpr:
        return _JSExpr(f"+{self._name}")

    # -- logical (Python `and`/`or` cannot be overloaded, so we provide ----)
    # -- methods for those)                                                 --

    def And(self, other: Any) -> _JSExpr:
        """``x.And(y)`` -> ``x && y``"""
        return _JSExpr(f"{self._name} && {_as_expr(other)}")

    def Or(self, other: Any) -> _JSExpr:
        """``x.Or(y)`` -> ``x || y``"""
        return _JSExpr(f"{self._name} || {_as_expr(other)}")

    def Not(self) -> _JSExpr:
        """``x.Not()`` -> ``!x``"""
        return _JSExpr(f"!{self._name}")

    # -- property / index access --------------------------------------------

    def prop(self, attr: str) -> _JSExpr:
        """``x.prop("length")`` -> ``x.length``"""
        return _JSExpr(f"{self._name}.{attr}")

    def idx(self, index: Any) -> _JSExpr:
        """``x.idx(0)`` -> ``x[0]``"""
        return _JSExpr(f"{self._name}[{_as_expr(index)}]")

    # -- method call --------------------------------------------------------

    def call(self, method: str, *args: Any) -> _JSExpr:
        """``x.call("push", 1)`` -> ``x.push(1)``"""
        arg_str = ", ".join(_as_expr(a) for a in args)
        return _JSExpr(f"{self._name}.{method}({arg_str})")

    # -- increment / decrement (common JS patterns) ------------------------

    def increment(self) -> "VarProxy":
        """Emit ``<name>++;``"""
        _flush_pending_close()
        _buf.add(f"{self._name}++;")
        return self

    def decrement(self) -> "VarProxy":
        """Emit ``<name>--;``"""
        _flush_pending_close()
        _buf.add(f"{self._name}--;")
        return self

    # -- optional chaining --------------------------------------------------

    def optchain(self, attr: str) -> _JSExpr:
        """``x.optchain("name")`` -> ``x?.name``"""
        return _JSExpr(f"{self._name}?.{attr}")

    def optidx(self, index: Any) -> _JSExpr:
        """``x.optidx(0)`` -> ``x?.[0]``"""
        return _JSExpr(f"{self._name}?.[{_as_expr(index)}]")

    def optcall(self, method: str, *args: Any) -> _JSExpr:
        """``x.optcall("toString")`` -> ``x?.toString()``"""
        arg_str = ", ".join(_as_expr(a) for a in args)
        return _JSExpr(f"{self._name}?.{method}({arg_str})")

    # -- nullish coalescing -------------------------------------------------

    def Nullish(self, other: Any) -> _JSExpr:
        """``x.Nullish(default)`` -> ``x ?? default``"""
        return _JSExpr(f"{self._name} ?? {_as_expr(other)}")

    def __repr__(self) -> str:
        return f"VarProxy({self._name!r})"


# ---------------------------------------------------------------------------
# _JSExpr operator overloads (so chained expressions like (x + 1) * 2 work)
# ---------------------------------------------------------------------------

def _patch_jsexpr():
    """Add operator overloads to _JSExpr so compound expressions work."""

    def _bin(op):
        def method(self, other):
            rhs = _as_expr(other)
            return _JSExpr(f"({self.expr} {op} {rhs})")
        return method

    def _rbin(op):
        def method(self, other):
            lhs = _as_expr(other)
            return _JSExpr(f"({lhs} {op} {self.expr})")
        return method

    def _unary(op):
        def method(self):
            return _JSExpr(f"({op}{self.expr})")
        return method

    _JSExpr.__add__ = _bin("+")
    _JSExpr.__radd__ = _rbin("+")
    _JSExpr.__sub__ = _bin("-")
    _JSExpr.__rsub__ = _rbin("-")
    _JSExpr.__mul__ = _bin("*")
    _JSExpr.__rmul__ = _rbin("*")
    _JSExpr.__truediv__ = _bin("/")
    _JSExpr.__rtruediv__ = _rbin("/")
    _JSExpr.__mod__ = _bin("%")
    _JSExpr.__pow__ = _bin("**")  # JS ** operator

    _JSExpr.__eq__ = _bin("===")   # type: ignore
    _JSExpr.__ne__ = _bin("!==")   # type: ignore
    _JSExpr.__lt__ = _bin("<")
    _JSExpr.__le__ = _bin("<=")
    _JSExpr.__gt__ = _bin(">")
    _JSExpr.__ge__ = _bin(">=")

    _JSExpr.__and__ = _bin("&")
    _JSExpr.__or__ = _bin("|")
    _JSExpr.__xor__ = _bin("^")
    _JSExpr.__lshift__ = _bin("<<")
    _JSExpr.__rshift__ = _bin(">>")
    _JSExpr.__invert__ = _unary("~")
    _JSExpr.__neg__ = _unary("-")
    _JSExpr.__pos__ = _unary("+")

    # Optional chaining on _JSExpr
    def _optchain(self, attr: str) -> _JSExpr:
        return _JSExpr(f"{self.expr}?.{attr}")
    _JSExpr.optchain = _optchain

    def _optidx(self, index: Any) -> _JSExpr:
        return _JSExpr(f"{self.expr}?.[{_as_expr(index)}]")
    _JSExpr.optidx = _optidx

    def _optcall(self, method: str, *args: Any) -> _JSExpr:
        arg_str = ", ".join(_as_expr(a) for a in args)
        return _JSExpr(f"{self.expr}?.{method}({arg_str})")
    _JSExpr.optcall = _optcall

    def _Nullish(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self.expr} ?? {_as_expr(other)}")
    _JSExpr.Nullish = _Nullish

    # Property / index / call on _JSExpr
    def _prop(self, attr: str) -> _JSExpr:
        return _JSExpr(f"{self.expr}.{attr}")
    _JSExpr.prop = _prop

    def _idx(self, index: Any) -> _JSExpr:
        return _JSExpr(f"{self.expr}[{_as_expr(index)}]")
    _JSExpr.idx = _idx

    def _call(self, method: str, *args: Any) -> _JSExpr:
        arg_str = ", ".join(_as_expr(a) for a in args)
        return _JSExpr(f"{self.expr}.{method}({arg_str})")
    _JSExpr.call = _call

    # Logical helpers on _JSExpr
    def _And(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self.expr} && {_as_expr(other)}")
    _JSExpr.And = _And

    def _Or(self, other: Any) -> _JSExpr:
        return _JSExpr(f"{self.expr} || {_as_expr(other)}")
    _JSExpr.Or = _Or

    def _Not(self) -> _JSExpr:
        return _JSExpr(f"!{self.expr}")
    _JSExpr.Not = _Not


_patch_jsexpr()


# ---------------------------------------------------------------------------
# Variable declarations: Let, Const, Var
# ---------------------------------------------------------------------------

def Let(name: str, value: Any = _UNSET, source: Any = _UNSET) -> VarProxy:
    """
    Declare a JavaScript ``let`` variable and return a ``VarProxy``.

    If *source* is provided, the declaration becomes a destructuring:
    ``let pattern = source;``

    Example::

        x = Let("x", 10)
        # -> let x = 10;

        y = Let("y")
        # -> let y;

        Let("props", DestructObj("name", "age"), JS("user"))
        # -> let {name, age} = user;

        Let("coords", DestructArr("x", "y"), JS("point"))
        # -> let [x, y] = point;
    """
    _flush_pending_close()
    proxy = VarProxy(name)
    if source is not _UNSET:
        # Destructuring form: let pattern = source;
        _buf.add(f"let {_as_expr(value)} = {_as_expr(source)};")
    elif value is not _UNSET:
        _buf.add(f"let {name} = {_as_expr(value)};")
    else:
        _buf.add(f"let {name};")
    return proxy


def Const(name: str, value: Any = _UNSET, source: Any = _UNSET) -> VarProxy:
    """
    Declare a JavaScript ``const`` variable and return a ``VarProxy``.

    If *source* is provided, the declaration becomes a destructuring:
    ``const pattern = source;``

    Example::

        PI = Const("PI", 3.14159)
        # -> const PI = 3.14159;

        Const("props", DestructObj("name", "age"), JS("user"))
        # -> const {name, age} = user;
    """
    _flush_pending_close()
    proxy = VarProxy(name)
    if source is not _UNSET:
        # Destructuring form: const pattern = source;
        _buf.add(f"const {_as_expr(value)} = {_as_expr(source)};")
    else:
        _buf.add(f"const {name} = {_as_expr(value)};")
    return proxy


def Var(name: str, value: Any = _UNSET, source: Any = _UNSET) -> VarProxy:
    """
    Declare a JavaScript ``var`` variable and return a ``VarProxy``.

    If *source* is provided, the declaration becomes a destructuring:
    ``var pattern = source;``

    Example::

        legacy = Var("count", 0)
        # -> var count = 0;

        Var("props", DestructObj("name"), JS("user"))
        # -> var {name} = user;
    """
    _flush_pending_close()
    proxy = VarProxy(name)
    if source is not _UNSET:
        # Destructuring form: var pattern = source;
        _buf.add(f"var {_as_expr(value)} = {_as_expr(source)};")
    elif value is not _UNSET:
        _buf.add(f"var {name} = {_as_expr(value)};")
    else:
        _buf.add(f"var {name};")
    return proxy


# ---------------------------------------------------------------------------
# Control flow: If / Elif / Else
# ---------------------------------------------------------------------------

class If:
    """
    Context manager for an ``if`` block.

    The body is automatically indented.  The closing brace is deferred
    until we know whether an ``Elif`` or ``Else`` follows.

    Example::

        with If(x > 10):
            Print("big")
    """

    def __init__(self, condition: Any) -> None:
        self._condition = condition

    def __enter__(self):
        _flush_pending_close()
        cond = _as_expr(self._condition)
        _buf.add(f"if ({cond}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _buf._indent_level -= 1
        # Defer closing brace — Elif/Else might follow
        global _pending_close
        _pending_close = True
        return False


class Elif:
    """
    Context manager for an ``elif`` block (must follow If or another Elif).

    Example::

        with Elif(x < 10):
            Print("small")
    """

    def __init__(self, condition: Any) -> None:
        self._condition = condition

    def __enter__(self):
        # Cancel the pending close — we handle it by emitting "} else if"
        global _pending_close
        _pending_close = False
        cond = _as_expr(self._condition)
        _buf.add(f"}} else if ({cond}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _buf._indent_level -= 1
        # Defer closing brace again
        global _pending_close
        _pending_close = True
        return False


class Else:
    """
    Context manager for an ``else`` block (must follow If or Elif).

    Example::

        with Else():
            Print("equal")
    """

    def __enter__(self):
        global _pending_close
        _pending_close = False
        _buf.add("} else {")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _buf._indent_level -= 1
        global _pending_close
        _pending_close = True
        return False


# ---------------------------------------------------------------------------
# Switch / Case / Default
# ---------------------------------------------------------------------------

class Switch:
    """
    Context manager for a ``switch`` statement.

    Example::

        day = Let("day", JS('"Monday"'))
        with Switch(day):
            with Case('"Monday"'):
                Print("Start of week")
                Break()
            with Case('"Friday"'):
                Print("Almost weekend")
                Break()
            with Default():
                Print("Midweek")
    """

    def __init__(self, expr: Any) -> None:
        self._expr = expr

    def __enter__(self):
        _flush_pending_close()
        expr_str = _as_expr(self._expr)
        _buf.add(f"switch ({expr_str}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("}")
        return False


class Case:
    """
    Context manager for a ``case`` block inside a ``switch``.

    Example::

        with Case('"Monday"'):
            Print("Start of week")
            Break()
    """

    def __init__(self, value: Any) -> None:
        self._value = value

    def __enter__(self):
        _flush_pending_close()
        val_str = _as_expr_raw(self._value)
        _buf.add(f"case {val_str}:")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _buf._indent_level -= 1
        return False


class Default:
    """
    Context manager for a ``default`` block inside a ``switch``.

    Example::

        with Default():
            Print("Unknown day")
            Break()
    """

    def __enter__(self):
        _flush_pending_close()
        _buf.add("default:")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _buf._indent_level -= 1
        return False


# ---------------------------------------------------------------------------
# While loop
# ---------------------------------------------------------------------------

class While:
    """Context manager for a ``while`` loop."""

    def __init__(self, condition: Any) -> None:
        self._condition = condition

    def __enter__(self):
        _flush_pending_close()
        cond = _as_expr(self._condition)
        _buf.add(f"while ({cond}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("}")
        return False


# ---------------------------------------------------------------------------
# For loop (classic C-style)
# ---------------------------------------------------------------------------

class For:
    """
    Context manager for a classic C-style ``for`` loop.

    The *init*, *condition*, and *update* arguments are treated as raw
    JavaScript fragments — they are emitted directly without quoting.

    Example::

        with For("let i = 0", "i < 10", "i++"):
            Print("i = ${i}")
    """

    def __init__(self, init: Any, condition: Any, update: Any) -> None:
        self._init = init
        self._condition = condition
        self._update = update

    def __enter__(self):
        _flush_pending_close()
        # For-loop headers are raw JS — use _as_expr_raw to avoid quoting strings
        init_str = _as_expr_raw(self._init)
        cond_str = _as_expr_raw(self._condition)
        update_str = _as_expr_raw(self._update)
        _buf.add(f"for ({init_str}; {cond_str}; {update_str}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("}")
        return False


# ---------------------------------------------------------------------------
# ForOf loop (for…of)
# ---------------------------------------------------------------------------

class ForOf:
    """
    Context manager for a ``for…of`` loop.

    Example::

        items = Let("items", [1, 2, 3])
        with ForOf("item", items):
            Print("item")
    """

    def __init__(self, var_name: str, iterable: Any) -> None:
        self._var_name = var_name
        self._iterable = iterable

    def __enter__(self):
        _flush_pending_close()
        iter_str = _as_expr(self._iterable)
        _buf.add(f"for (let {self._var_name} of {iter_str}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("}")
        return False


# ---------------------------------------------------------------------------
# ForIn loop (for…in)
# ---------------------------------------------------------------------------

class ForIn:
    """
    Context manager for a ``for…in`` loop.

    Example::

        obj = Let("obj", {"a": 1, "b": 2})
        with ForIn("key", obj):
            Print("key")
    """

    def __init__(self, var_name: str, obj: Any) -> None:
        self._var_name = var_name
        self._obj = obj

    def __enter__(self):
        _flush_pending_close()
        obj_str = _as_expr(self._obj)
        _buf.add(f"for (let {self._var_name} in {obj_str}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _buf._indent_level -= 1
        _buf.add("}")
        return False


# ---------------------------------------------------------------------------
# Function declaration
# ---------------------------------------------------------------------------

class Func:
    """
    Context manager for a JavaScript function declaration.

    Example::

        with Func("greet", "name"):
            Print("Hello, ${name}!")
    """

    def __init__(self, name: str, *params: str) -> None:
        self._name = name
        self._params = params

    def __enter__(self):
        _flush_pending_close()
        param_str = ", ".join(self._params)
        _buf.add(f"function {self._name}({param_str}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("}")
        return False


# ---------------------------------------------------------------------------
# Arrow function (expression)
# ---------------------------------------------------------------------------

class ArrowFunc:
    """
    Context manager for a JavaScript arrow function assigned to a variable.

    Example::

        with ArrowFunc("add", "a", "b"):
            Return("a + b")
        # -> const add = (a, b) => {
        #        return a + b;
        #    };
    """

    def __init__(self, name: str, *params: str) -> None:
        self._name = name
        self._params = params

    def __enter__(self):
        _flush_pending_close()
        param_str = ", ".join(self._params)
        _buf.add(f"const {self._name} = ({param_str}) => {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("};")
        return False


# ---------------------------------------------------------------------------
# Async function declaration
# ---------------------------------------------------------------------------

class AsyncFunc:
    """
    Context manager for an ``async function`` declaration.

    Supports both ``with`` (sync) and ``async with`` (async) Python syntax.

    Example::

        with AsyncFunc("fetchData", "url"):
            data = Let("data", Await(JS("fetch(url)")))
            Return(JS("data"))
    """

    def __init__(self, name: str, *params: str) -> None:
        self._name = name
        self._params = params

    def __enter__(self):
        _flush_pending_close()
        param_str = ", ".join(self._params)
        _buf.add(f"async function {self._name}({param_str}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("}")
        return False

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


# ---------------------------------------------------------------------------
# Async arrow function
# ---------------------------------------------------------------------------

class AsyncArrowFunc:
    """
    Context manager for an ``async`` arrow function assigned to a ``const``.

    Supports both ``with`` and ``async with``.
    """

    def __init__(self, name: str, *params: str) -> None:
        self._name = name
        self._params = params

    def __enter__(self):
        _flush_pending_close()
        param_str = ", ".join(self._params)
        _buf.add(f"const {self._name} = async ({param_str}) => {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("};")
        return False

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


# ---------------------------------------------------------------------------
# Await — produce a JavaScript ``await`` expression
# ---------------------------------------------------------------------------

class Await:
    """
    Represents a JavaScript ``await`` expression.

    Can be used inline in Let/Return/etc or as a standalone statement.
    """

    def __init__(self, expr: Any) -> None:
        self._expr = expr
        self._js_expr = _JSExpr(f"await {_as_expr(self._expr)}")

    def __repr__(self) -> str:
        return f"Await({self._js_expr.expr!r})"

    @property
    def expr(self) -> str:
        """The raw JavaScript expression string, e.g. ``await fetch(url)``."""
        return self._js_expr.expr

    def __await__(self):
        """Allow ``await Await(...)`` inside an ``async def``."""
        _flush_pending_close()
        _buf.add(f"{self.expr};")
        yield
        return self._js_expr

    def emit(self) -> None:
        """Emit ``await <expr>;`` as a standalone statement."""
        _flush_pending_close()
        _buf.add(f"{self.expr};")


# ---------------------------------------------------------------------------
# ForAwait — for await…of loop
# ---------------------------------------------------------------------------

class ForAwait:
    """
    Context manager for a ``for await…of`` loop (async iteration).

    Example::

        stream = Let("stream", JS("getReadableStream()"))
        with ForAwait("chunk", stream):
            Print("chunk = ${chunk}")
    """

    def __init__(self, var_name: str, iterable: Any) -> None:
        self._var_name = var_name
        self._iterable = iterable

    def __enter__(self):
        _flush_pending_close()
        iter_str = _as_expr(self._iterable)
        _buf.add(f"for await (let {self._var_name} of {iter_str}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("}")
        return False

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


# ---------------------------------------------------------------------------
# Try / Catch / Finally
# ---------------------------------------------------------------------------

class Try:
    """
    Context manager for a ``try`` block.

    Must be followed by ``with Catch(…)`` and/or ``with Finally()``.
    """

    def __enter__(self):
        _flush_pending_close()
        _buf.add("try {")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        global _pending_close
        _pending_close = True
        return False

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


class Catch:
    """
    Context manager for a ``catch`` block (must follow ``Try``).
    """

    def __init__(self, error_var: str = "err") -> None:
        self._error_var = error_var

    def __enter__(self):
        global _pending_close
        _pending_close = False
        _buf.add(f"}} catch ({self._error_var}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _buf._indent_level -= 1
        global _pending_close
        _pending_close = True
        return False

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


class Finally:
    """
    Context manager for a ``finally`` block (must follow ``Try`` or ``Catch``).
    """

    def __enter__(self):
        global _pending_close
        _pending_close = False
        _buf.add("} finally {")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _buf._indent_level -= 1
        global _pending_close
        _pending_close = True
        return False

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


# ---------------------------------------------------------------------------
# Throw
# ---------------------------------------------------------------------------

def Throw(value: Any) -> None:
    """
    Emit a ``throw`` statement.

    Example::

        Throw(JS("new Error('something went wrong')"))
    """
    _flush_pending_close()
    _buf.add(f"throw {_as_expr(value)};")


# ---------------------------------------------------------------------------
# New — produce a JavaScript ``new`` expression
# ---------------------------------------------------------------------------

def New(class_name: str, *args: Any) -> _JSExpr:
    """
    Create a ``new ClassName(args)`` expression.

    Returns a ``_JSExpr`` — does **not** emit anything by itself.
    Use it inside ``Let``, ``Return``, ``Const``, etc.
    """
    arg_str = ", ".join(_as_expr(a) for a in args)
    return _JSExpr(f"new {class_name}({arg_str})")


# ---------------------------------------------------------------------------
# Return
# ---------------------------------------------------------------------------

def Return(value: Any = None) -> None:
    """Emit a ``return`` statement."""
    _flush_pending_close()
    if value is not None:
        _buf.add(f"return {_as_expr(value)};")
    else:
        _buf.add("return;")


# ---------------------------------------------------------------------------
# Print -> console.log
# ---------------------------------------------------------------------------

def Print(*values: Any) -> None:
    """
    Emit ``console.log(…)``.

    If a single string argument contains ``${…}`` it is emitted as a
    template literal. Multiple arguments are passed to ``console.log``
    separated by commas.
    """
    _flush_pending_close()
    if len(values) == 1:
        _buf.add(f"console.log({_js_repr(values[0])});")
    else:
        parts = ", ".join(_js_repr(v) for v in values)
        _buf.add(f"console.log({parts});")


# ---------------------------------------------------------------------------
# FnCall — call a JavaScript function
# ---------------------------------------------------------------------------

def FnCall(name: str, *args: Any) -> None:
    """
    Emit a bare function call statement.

    Example::

        FnCall("alert", "Hello!")
        # -> alert("Hello!");
    """
    _flush_pending_close()
    arg_str = ", ".join(_as_expr(a) for a in args)
    _buf.add(f"{name}({arg_str});")


# ---------------------------------------------------------------------------
# Raw — inject raw JavaScript
# ---------------------------------------------------------------------------

def Raw(js: str) -> None:
    """
    Inject raw JavaScript code (one or more lines) into the output.

    Each line is emitted at the current indentation level.
    """
    _flush_pending_close()
    for line in js.split("\n"):
        _buf.add(line)


# ---------------------------------------------------------------------------
# Break / Continue
# ---------------------------------------------------------------------------

def Break() -> None:
    """Emit ``break;``"""
    _flush_pending_close()
    _buf.add("break;")


def Continue() -> None:
    """Emit ``continue;``"""
    _flush_pending_close()
    _buf.add("continue;")


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------

def Comment(text: str) -> None:
    """
    Emit a single-line JavaScript comment.

    Example::

        Comment("This is a note")
        # -> // This is a note
    """
    _flush_pending_close()
    _buf.add(f"// {text}")


# ===========================================================================
# NEW FEATURES — Classes, Destructuring, Spread/Rest, Switch, Objects,
#   Optional Chaining, Nullish Coalescing, Modules, Tagged Templates,
#   Generators, Private Fields
# ===========================================================================


# ---------------------------------------------------------------------------
# Classes — class declaration with constructor, methods, getters/setters,
#           extends, super, private fields
# ---------------------------------------------------------------------------

class Class:
    """
    Context manager for a JavaScript ``class`` declaration.

    Supports ``extends``, ``constructor``, methods, getters, setters,
    private fields (``#field``), and static members.

    Inside the class body, use:

    - ``ClassConstructor(*params)`` for the constructor
    - ``ClassMethod("name", *params)`` for instance methods
    - ``ClassStaticMethod("name", *params)`` for static methods
    - ``Getter("name")`` / ``Setter("name", "param")`` for accessors
    - ``PrivateField("#name", value)`` for private field declarations
    - ``StaticField("name", value)`` for static field declarations

    Example::

        with Class("Animal", extends="EventEmitter"):
            with ClassConstructor("name", "sound"):
                    This("name").set(JS("name"))
                    This("sound").set(JS("sound"))
                with ClassMethod("speak"):
                    Print("${this.name} says ${this.sound}")
    """

    def __init__(self, name: str, extends: str = "") -> None:
        self._name = name
        self._extends = extends

    def __enter__(self):
        _flush_pending_close()
        if self._extends:
            _buf.add(f"class {self._name} extends {self._extends} {{")
        else:
            _buf.add(f"class {self._name} {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("}")
        return False


class _ClassMember:
    """Base class for class members that manage pending close for method bodies."""

    def _open_method(self, header: str) -> None:
        _flush_pending_close()
        _buf.add(header)
        _buf._indent_level += 1

    def _close_method(self) -> None:
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("}")


class ClassConstructor(_ClassMember):
    """
    Context manager for a ``constructor`` inside a ``Class``.

    Example::

        with ClassConstructor("name", "age"):
            Super("Person", "name")
            This("age").set(JS("age"))
    """

    def __init__(self, *params: str) -> None:
        self._params = params

    def __enter__(self):
        param_str = ", ".join(self._params)
        self._open_method(f"constructor({param_str}) {{")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_method()
        return False


class ClassMethod(_ClassMember):
    """
    Context manager for an instance method inside a ``Class``.

    Example::

        with ClassMethod("greet"):
            Print("Hello!")
    """

    def __init__(self, name: str, *params: str) -> None:
        self._name = name
        self._params = params

    def __enter__(self):
        param_str = ", ".join(self._params)
        self._open_method(f"{self._name}({param_str}) {{")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_method()
        return False


class ClassStaticMethod(_ClassMember):
    """
    Context manager for a static method inside a ``Class``.

    Example::

        with ClassStaticMethod("create", "name"):
            Return(New("Person", JS("name")))
    """

    def __init__(self, name: str, *params: str) -> None:
        self._name = name
        self._params = params

    def __enter__(self):
        param_str = ", ".join(self._params)
        self._open_method(f"static {self._name}({param_str}) {{")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_method()
        return False


class Getter(_ClassMember):
    """
    Context manager for a ``get`` accessor inside a ``Class``.

    Example::

        with Getter("fullName"):
            Return(JS("this.firstName + ' ' + this.lastName"))
    """

    def __init__(self, name: str) -> None:
        self._name = name

    def __enter__(self):
        self._open_method(f"get {self._name}() {{")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_method()
        return False


class Setter(_ClassMember):
    """
    Context manager for a ``set`` accessor inside a ``Class``.

    Example::

        with Setter("name", "value"):
            This("_name").set(JS("value"))
    """

    def __init__(self, name: str, param: str = "value") -> None:
        self._name = name
        self._param = param

    def __enter__(self):
        self._open_method(f"set {self._name}({self._param}) {{")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_method()
        return False


def This(attr: str = "") -> VarProxy:
    """
    Create a VarProxy for ``this`` or ``this.attr``.

    Example::

        This("name").set(JS("name"))
        # -> this.name = name;

        This().call("render")
        # -> this.render()
    """
    if attr:
        return VarProxy(f"this.{attr}")
    return VarProxy("this")


def Super(*args: Any) -> None:
    """
    Emit a ``super(...)`` call (typically inside a constructor).

    Arguments are treated as raw JS fragments — strings are NOT quoted.
    Use ``JS()`` for complex expressions.

    Example::

        Super(JS("name"))
        # -> super(name);

        Super("name", "age")
        # -> super(name, age);
    """
    _flush_pending_close()
    arg_str = ", ".join(_as_expr_raw(a) for a in args)
    _buf.add(f"super({arg_str});")


def PrivateField(name: str, value: Any = _UNSET) -> None:
    """
    Declare a private class field (``#field``).

    The *name* should include the ``#`` prefix.

    Example::

        PrivateField("#age", 0)
        # -> #age = 0;

        PrivateField("#name")
        # -> #name;
    """
    _flush_pending_close()
    if value is not _UNSET:
        _buf.add(f"{name} = {_as_expr(value)};")
    else:
        _buf.add(f"{name};")


def StaticField(name: str, value: Any = _UNSET) -> None:
    """
    Declare a static class field.

    Example::

        StaticField("count", 0)
        # -> static count = 0;

        StaticField("#privateStatic", 42)
        # -> static #privateStatic = 42;
    """
    _flush_pending_close()
    if value is not _UNSET:
        _buf.add(f"static {name} = {_as_expr(value)};")
    else:
        _buf.add(f"static {name};")


# ---------------------------------------------------------------------------
# Destructuring — const {a, b} = obj, const [x, y] = arr
# ---------------------------------------------------------------------------

class _DestructExpr:
    """Internal: represents a destructuring pattern as a JS expression."""

    def __init__(self, js: str) -> None:
        self._js_str = js

    def _js(self) -> str:
        return self._js_str


def DestructObj(*names: str, **aliases: str) -> _DestructExpr:
    """
    Create an object destructuring pattern.

    Positional args are plain names: ``DestructObj("a", "b")`` → ``{a, b}``
    Keyword args are aliases: ``DestructObj(x="y")`` → ``{y: x}``
    Mix both: ``DestructObj("a", b="renamedB")`` → ``{a, renamedB: b}``

    Example::

        Const("props", DestructObj("name", "age"), JS("user"))
        # -> const {name, age} = user;

        Const("data", DestructObj("name", val="value"), JS("config"))
        # -> const {name, value: val} = config;
    """
    parts: list[str] = []
    for name in names:
        parts.append(name)
    for alias, source in aliases.items():
        parts.append(f"{source}: {alias}")
    return _DestructExpr("{" + ", ".join(parts) + "}")


def DestructArr(*names: str) -> _DestructExpr:
    """
    Create an array destructuring pattern.

    Example::

        Const("coords", DestructArr("x", "y"), JS("point"))
        # -> const [x, y] = point;

        Let("first", DestructArr("a", "...rest"), JS("items"))
        # -> let [a, ...rest] = items;
    """
    parts: list[str] = []
    for name in names:
        if name.startswith("..."):
            parts.append(f"...{name[3:]}")
        else:
            parts.append(name)
    return _DestructExpr("[" + ", ".join(parts) + "]")


# ---------------------------------------------------------------------------
# Spread / Rest — ...args, [...arr], {...obj}
# ---------------------------------------------------------------------------

class Spread:
    """
    Represents a JavaScript spread/rest ``...expr``.

    Use as a value in Let/Const/arrays/objects or as a function argument.

    Example::

        Let("arr", [1, 2, Spread(JS("more"))])
        # -> let arr = [1, 2, ...more];

        Let("merged", {"a": 1, **{}})
        # Using Spread:
        Let("merged", Obj(spread=JS("defaults"), b=2))
    """

    def __init__(self, expr: Any) -> None:
        self._expr = expr

    def _js(self) -> str:
        return f"...{_as_expr(self._expr)}"


# ---------------------------------------------------------------------------
# Object literal builder — shorthand, computed keys, method syntax
# ---------------------------------------------------------------------------

class Obj:
    """
    Build a JavaScript object literal expression.

    Supports regular keys, shorthand keys, computed keys, method syntax,
    spread, and getter/setter shorthand.

    Regular key-value pairs are passed as keyword arguments.
    Shorthand keys are passed via the ``shorthand`` parameter.
    Computed keys are passed via the ``computed`` dict.
    Method entries via ``methods``.
    Spread entries via ``spreads``.
    Getter/setter via ``getters``/``setters``.

    Returns a ``_JSExpr`` — does **not** emit anything by itself.
    Use it inside ``Let``, ``Const``, ``Return``, etc.

    Example::

        name = Let("name", JS("'Alice'"))
        age = Let("age", 30)

        obj = Let("obj", Obj(name=name, age=age))
        # -> let obj = {name, age};      (shorthand when key matches var name)

        Let("data", Obj(x=1, y=2))
        # -> let data = {x: 1, y: 2};

        Let("dyn", Obj(computed={"[keyVar]": 42}))
        # -> let dyn = {[keyVar]: 42};

        Let("withMethod", Obj(methods={"greet": "name"}))
        # -> let withMethod = {greet(name) { ... }};

        Let("merged", Obj(spreads=[JS("defaults")], x=1))
        # -> let merged = {...defaults, x: 1};
    """

    def __init__(
        self,
        shorthand: list[Any] | None = None,
        computed: dict[str, Any] | None = None,
        methods: dict[str, str] | None = None,
        spreads: list[Any] | None = None,
        getters: dict[str, str] | None = None,
        setters: dict[str, str] | None = None,
        **kv_pairs: Any,
    ) -> None:
        self._shorthand = shorthand or []
        self._computed = computed or {}
        self._methods = methods or {}
        self._spreads = spreads or []
        self._getters = getters or {}
        self._setters = setters or {}
        self._kv = kv_pairs

    def _js(self) -> str:
        parts: list[str] = []

        # Spread entries
        for sp in self._spreads:
            parts.append(f"...{_as_expr(sp)}")

        # Regular key-value pairs
        for key, value in self._kv.items():
            # Check if value is a VarProxy with matching name -> shorthand
            if isinstance(value, VarProxy) and value._name == key:
                parts.append(key)
            else:
                parts.append(f"{key}: {_as_expr(value)}")

        # Shorthand entries (just the key name)
        for s in self._shorthand:
            if isinstance(s, VarProxy):
                parts.append(s._name)
            else:
                parts.append(str(s))

        # Computed keys
        for comp_key, value in self._computed.items():
            parts.append(f"{comp_key}: {_as_expr(value)}")

        # Method syntax: name(params) { body } — but we can't express body inline
        # So we just output the method signature with empty body
        for method_name, params in self._methods.items():
            parts.append(f"{method_name}({params}) {{ }}")

        # Getter syntax
        for getter_name, body_expr in self._getters.items():
            parts.append(f"get {getter_name}() {{ return {_as_expr(body_expr)}; }}")

        # Setter syntax
        for setter_name, param in self._setters.items():
            parts.append(f"set {setter_name}({param}) {{ }}")

        return "{" + ", ".join(parts) + "}"


def ObjMethod(name: str, *params: str) -> _JSExpr:
    """
    Create a method expression for use inside Obj.

    Returns a raw JS fragment like ``name(params)`` — typically used
    with Obj's computed representation or Raw.

    For full method bodies inside Obj, prefer using ``Raw()`` inside
    a ``with Class():`` block, or construct the object using ``Raw()``.
    """
    param_str = ", ".join(params)
    return _JSExpr(f"{name}({param_str})")


# ---------------------------------------------------------------------------
# Optional chaining (?.) and nullish coalescing (??)
# ---------------------------------------------------------------------------

# These are already methods on VarProxy and _JSExpr:
#   x.optchain("name")     -> x?.name
#   x.optidx(0)            -> x?.[0]
#   x.optcall("toString")  -> x?.toString()
#   x.Nullish(default)     -> x ?? default

# Standalone helper functions for expressions:

def OptChain(expr: Any, attr: str) -> _JSExpr:
    """
    Create an optional chaining expression: ``expr?.attr``.

    Example::

        Let("name", OptChain(JS("user"), "name"))
        # -> let name = user?.name;
    """
    return _JSExpr(f"{_as_expr(expr)}?.{attr}")


def OptIdx(expr: Any, index: Any) -> _JSExpr:
    """
    Create an optional index expression: ``expr?.[index]``.

    Example::

        Let("first", OptIdx(JS("items"), 0))
        # -> let first = items?.[0];
    """
    return _JSExpr(f"{_as_expr(expr)}?.[{_as_expr(index)}]")


def Nullish(expr: Any, default: Any) -> _JSExpr:
    """
    Create a nullish coalescing expression: ``expr ?? default``.

    Example::

        Let("val", Nullish(JS("input"), 0))
        # -> let val = input ?? 0;
    """
    return _JSExpr(f"{_as_expr(expr)} ?? {_as_expr(default)}")


# ---------------------------------------------------------------------------
# Modules — import / export
# ---------------------------------------------------------------------------

def Import(module: str, *names: str, default: str = "", module_alias: str = "") -> None:
    """
    Emit an import statement.

    Several forms are supported:

    1. Named imports::

        Import("lodash", "debounce", "throttle")
        # -> import {debounce, throttle} from "lodash";

    2. Default import::

        Import("react", default="React")
        # -> import React from "react";

    3. Default + named::

        Import("react", "useState", "useEffect", default="React")
        # -> import React, {useState, useEffect} from "react";

    4. Namespace import::

        Import("lodash", module_alias="_")
        # -> import * as _ from "lodash";

    5. Side-effect import::

        Import("./side-effects.js")
        # -> import "./side-effects.js";
    """
    _flush_pending_close()

    if not names and not default and not module_alias:
        # Side-effect import
        _buf.add(f'import "{module}";')
        return

    if module_alias:
        # Namespace import
        _buf.add(f'import * as {module_alias} from "{module}";')
        return

    parts = ""
    if default:
        parts = default
    if names:
        named = ", ".join(names)
        if default:
            parts += f", {{{named}}}"
        else:
            parts = f"{{{named}}}"

    _buf.add(f"import {parts} from \"{module}\";")


def ImportDynamic(module: str) -> _JSExpr:
    """
    Create a dynamic import expression: ``import("module")``.

    Returns a ``_JSExpr`` — use inside Let/Await/etc.

    Example::

        Let("mod", Await(ImportDynamic("./myModule.js")))
        # -> let mod = await import("./myModule.js");
    """
    return _JSExpr(f'import("{module}")')


def Export(*names: str) -> None:
    """
    Emit a named export statement.

    Example::

        Export("add", "subtract")
        # -> export {add, subtract};

        Export("default", "MyComponent")
        # -> export {MyComponent as default};
    """
    _flush_pending_close()
    name_list = ", ".join(names)
    _buf.add(f"export {{{name_list}}};")


def ExportDefault(name: str = "", expr: Any = _UNSET) -> None:
    """
    Emit a default export statement.

    Two forms:

    1. Export an identifier::

        ExportDefault("MyClass")
        # -> export default MyClass;

    2. Export an expression::

        ExportDefault(expr=JS("{ foo: 1 }"))
        # -> export default { foo: 1 };
    """
    _flush_pending_close()
    if expr is not _UNSET:
        _buf.add(f"export default {_as_expr(expr)};")
    else:
        _buf.add(f"export default {name};")


# ---------------------------------------------------------------------------
# Tagged template literals
# ---------------------------------------------------------------------------

def TaggedTemplate(tag: str, *parts: str) -> _JSExpr:
    """
    Create a tagged template literal expression.

    The *tag* is the tag function name, and *parts* are the string
    segments of the template.  Use ``${…}`` within the parts for
    interpolation markers — they will be preserved as-is in the
    template literal.

    Example::

        Let("result", TaggedTemplate("html", "<div>${content}</div>"))
        # -> let result = html`<div>${content}</div>`;

        Let("styled", TaggedTemplate("css", "color: ${color};"))
        # -> let styled = css`color: ${color};`;
    """
    # Join parts into a single template string
    template = "".join(parts)
    # Escape backticks
    escaped = template.replace("`", "\\`")
    return _JSExpr(f"{tag}`{escaped}`")


# ---------------------------------------------------------------------------
# Generators — function*, yield, yield*
# ---------------------------------------------------------------------------

class GeneratorFunc:
    """
    Context manager for a JavaScript generator function ``function*``.

    Example::

        with GeneratorFunc("range", "start", "end"):
            i = Let("i", JS("start"))
            with While(i < JS("end")):
                Yield(i)
                i.set(i + 1)

        # -> function* range(start, end) {
        #        let i = start;
        #        while (i < end) {
        #            yield i;
        #            i = i + 1;
        #        }
        #    }
    """

    def __init__(self, name: str, *params: str) -> None:
        self._name = name
        self._params = params

    def __enter__(self):
        _flush_pending_close()
        param_str = ", ".join(self._params)
        _buf.add(f"function* {self._name}({param_str}) {{")
        _buf._indent_level += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _flush_pending_close()
        _buf._indent_level -= 1
        _buf.add("}")
        return False


def Yield(value: Any = None) -> None:
    """
    Emit a ``yield`` statement.

    Example::

        Yield(i)
        # -> yield i;

        Yield()
        # -> yield;
    """
    _flush_pending_close()
    if value is not None:
        _buf.add(f"yield {_as_expr(value)};")
    else:
        _buf.add("yield;")


def YieldFrom(iterable: Any) -> None:
    """
    Emit a ``yield*`` statement (delegating to another iterable).

    Example::

        YieldFrom(JS("anotherGenerator()"))
        # -> yield* anotherGenerator();
    """
    _flush_pending_close()
    _buf.add(f"yield* {_as_expr(iterable)};")


# ---------------------------------------------------------------------------
# JavaScript — the top-level output manager
# ---------------------------------------------------------------------------

class JavaScript:
    """
    Static class that provides output and utility methods for the
    generated JavaScript code.
    """

    @staticmethod
    def save_this_file(filename: str) -> None:
        """Write the accumulated JavaScript to *filename*."""
        _flush_pending_close()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(_buf.output())

    @staticmethod
    def to_string() -> str:
        """Return the accumulated JavaScript as a string."""
        _flush_pending_close()
        return _buf.output()

    @staticmethod
    def reset() -> None:
        """Clear the buffer and reset indentation."""
        global _pending_close
        _buf.reset()
        _pending_close = False

    @staticmethod
    def add_blank() -> None:
        """Emit a blank line in the JavaScript output."""
        _flush_pending_close()
        _buf.add_blank()
