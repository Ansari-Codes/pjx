"""
Comprehensive test suite for PJx.
"""
from pjx import *

def test_let():
    JavaScript.reset()
    x = Let("x", 10)
    assert JavaScript.to_string().strip() == "let x = 10;"
    print("  PASS: Let")


def test_const():
    JavaScript.reset()
    pi = Const("PI", 3.14)
    assert JavaScript.to_string().strip() == "const PI = 3.14;"
    print("  PASS: Const")


def test_var():
    JavaScript.reset()
    c = Var("count", 0)
    assert JavaScript.to_string().strip() == "var count = 0;"
    print("  PASS: Var")


def test_let_no_value():
    JavaScript.reset()
    x = Let("x")
    assert JavaScript.to_string().strip() == "let x;"
    print("  PASS: Let without value")


def test_if_elif_else():
    JavaScript.reset()
    x = Let("x", 10)
    with If(x > 10):
        Print("big")
    with Elif(x < 10):
        Print("small")
    with Else():
        Print("equal")

    expected = 'let x = 10;\nif (x > 10) {\n    console.log("big");\n} else if (x < 10) {\n    console.log("small");\n} else {\n    console.log("equal");\n}'
    assert JavaScript.to_string().strip() == expected
    print("  PASS: If/Elif/Else")


def test_if_only():
    JavaScript.reset()
    x = Let("x", 5)
    with If(x > 3):
        Print("yes")

    expected = 'let x = 5;\nif (x > 3) {\n    console.log("yes");\n}'
    assert JavaScript.to_string().strip() == expected
    print("  PASS: If only")


def test_if_else():
    JavaScript.reset()
    x = Let("x", 5)
    with If(x > 10):
        Print("big")
    with Else():
        Print("not big")

    expected = 'let x = 5;\nif (x > 10) {\n    console.log("big");\n} else {\n    console.log("not big");\n}'
    assert JavaScript.to_string().strip() == expected
    print("  PASS: If/Else")


def test_while():
    JavaScript.reset()
    y = Let("y", 0)
    with While(y < 10):
        y.set(y + 1)

    expected = "let y = 0;\nwhile (y < 10) {\n    y = y + 1;\n}"
    assert JavaScript.to_string().strip() == expected
    print("  PASS: While")


def test_for():
    JavaScript.reset()
    with For("let i = 0", "i < 5", "i++"):
        Print("i = ${i}")

    expected = "for (let i = 0; i < 5; i++) {\n    console.log(`i = ${i}`);\n}"
    assert JavaScript.to_string().strip() == expected
    print("  PASS: For")


def test_for_of():
    JavaScript.reset()
    items = Let("items", [1, 2, 3])
    with ForOf("item", items):
        Print("item")

    expected = 'let items = [1, 2, 3];\nfor (let item of items) {\n    console.log("item");\n}'
    assert JavaScript.to_string().strip() == expected
    print("  PASS: ForOf")


def test_for_in():
    JavaScript.reset()
    obj = Let("obj", {"a": 1})
    with ForIn("key", obj):
        Print("key")

    expected = 'let obj = {a: 1};\nfor (let key in obj) {\n    console.log("key");\n}'
    assert JavaScript.to_string().strip() == expected
    print("  PASS: ForIn")


def test_func():
    JavaScript.reset()
    with Func("greet", "name"):
        Print("Hello, ${name}!")
        Return(JS("name"))

    expected = "function greet(name) {\n    console.log(`Hello, ${name}!`);\n    return name;\n}"
    assert JavaScript.to_string().strip() == expected
    print("  PASS: Func")


def test_arrow_func():
    JavaScript.reset()
    with ArrowFunc("add", "a", "b"):
        Return(JS("a + b"))

    expected = "const add = (a, b) => {\n    return a + b;\n};"
    assert JavaScript.to_string().strip() == expected
    print("  PASS: ArrowFunc")


def test_print_template():
    JavaScript.reset()
    Print("value is ${x}")

    assert JavaScript.to_string().strip() == "console.log(`value is ${x}`);"
    print("  PASS: Print with template")


def test_print_plain():
    JavaScript.reset()
    Print("hello world")

    assert JavaScript.to_string().strip() == 'console.log("hello world");'
    print("  PASS: Print plain string")


def test_fncall():
    JavaScript.reset()
    FnCall("alert", "Hello!")

    assert JavaScript.to_string().strip() == 'alert("Hello!");'
    print("  PASS: FnCall")


def test_raw():
    JavaScript.reset()
    Raw("console.log('raw');")

    assert JavaScript.to_string().strip() == "console.log('raw');"
    print("  PASS: Raw")


def test_break_continue():
    JavaScript.reset()
    Break()
    assert JavaScript.to_string().strip() == "break;"

    JavaScript.reset()
    Continue()
    assert JavaScript.to_string().strip() == "continue;"
    print("  PASS: Break/Continue")


def test_comment():
    JavaScript.reset()
    Comment("A note")

    assert JavaScript.to_string().strip() == "// A note"
    print("  PASS: Comment")


def test_varproxy_set():
    JavaScript.reset()
    x = Let("x", 5)
    x.set(x + 10)

    expected = "let x = 5;\nx = x + 10;"
    assert JavaScript.to_string().strip() == expected
    print("  PASS: VarProxy.set")


def test_varproxy_increment_decrement():
    JavaScript.reset()
    x = Let("x", 0)
    x.increment()
    x.decrement()

    expected = "let x = 0;\nx++;\nx--;"
    assert JavaScript.to_string().strip() == expected
    print("  PASS: VarProxy increment/decrement")


def test_varproxy_operators():
    JavaScript.reset()
    x = Let("x", 0)
    # Test that operators return _JSExpr with correct JS strings
    assert (x + 5).expr == "x + 5"
    assert (x - 3).expr == "x - 3"
    assert (x * 2).expr == "x * 2"
    assert (x / 4).expr == "x / 4"
    assert (x % 7).expr == "x % 7"
    assert (x > 10).expr == "x > 10"
    assert (x < 10).expr == "x < 10"
    assert (x >= 10).expr == "x >= 10"
    assert (x <= 10).expr == "x <= 10"
    assert (x == 10).expr == "x === 10"
    assert (x != 10).expr == "x !== 10"
    assert (-x).expr == "-x"
    assert x.And(True).expr == "x && true"
    assert x.Or(False).expr == "x || false"
    assert x.Not().expr == "!x"
    print("  PASS: VarProxy operators")


def test_js_helper():
    JavaScript.reset()
    Return(JS("a + b"))

    assert JavaScript.to_string().strip() == "return a + b;"
    print("  PASS: JS helper")


def test_nested_if_in_while():
    JavaScript.reset()
    n = Let("n", 0)
    with While(n < 5):
        with If(n == 0):
            Print("zero")
        with Else():
            Print("nonzero")
        n.set(n + 1)

    expected = 'let n = 0;\nwhile (n < 5) {\n    if (n === 0) {\n        console.log("zero");\n    } else {\n        console.log("nonzero");\n    }\n    n = n + 1;\n}'
    assert JavaScript.to_string().strip() == expected
    print("  PASS: Nested If in While")


def test_full_example():
    """Test the exact example from the README."""
    JavaScript.reset()
    x = Let("x", 10)

    with If(x > 10):
        Print("x is greater than 10 with value ${x}.")
    with Elif(x < 10):
        Print("Nope, it is smaller with the value of ${x}.")
    with Else():
        Print("Ah! It is equal to ${x}.")

    y = Let("y", 0)

    with While(y < 10):
        y.set(y + 1)

    Print("Final value of y is ${y}.")

    expected = 'let x = 10;\nif (x > 10) {\n    console.log(`x is greater than 10 with value ${x}.`);\n} else if (x < 10) {\n    console.log(`Nope, it is smaller with the value of ${x}.`);\n} else {\n    console.log(`Ah! It is equal to ${x}.`);\n}\nlet y = 0;\nwhile (y < 10) {\n    y = y + 1;\n}\nconsole.log(`Final value of y is ${y}.`);'
    assert JavaScript.to_string().strip() == expected
    print("  PASS: Full README example")


def test_bool_none():
    JavaScript.reset()
    Let("flag", True)
    Let("nothing", None)

    expected = "let flag = true;\nlet nothing = null;"
    assert JavaScript.to_string().strip() == expected
    print("  PASS: Bool and None values")


def test_array_dict():
    JavaScript.reset()
    Let("arr", [1, 2, 3])
    Let("obj", {"key": "value"})

    expected = 'let arr = [1, 2, 3];\nlet obj = {key: "value"};'
    assert JavaScript.to_string().strip() == expected
    print("  PASS: Array and Dict values")


def test_varproxy_prop_idx_call():
    JavaScript.reset()
    arr = Let("arr", [])
    assert arr.prop("length").expr == "arr.length"
    assert arr.idx(0).expr == "arr[0]"
    assert arr.call("push", 42).expr == "arr.push(42)"
    print("  PASS: VarProxy prop/idx/call")


if __name__ == "__main__":
    print("=" * 50)
    print("PJx Test Suite")
    print("=" * 50)

    test_let()
    test_const()
    test_var()
    test_let_no_value()
    test_if_elif_else()
    test_if_only()
    test_if_else()
    test_while()
    test_for()
    test_for_of()
    test_for_in()
    test_func()
    test_arrow_func()
    test_print_template()
    test_print_plain()
    test_fncall()
    test_raw()
    test_break_continue()
    test_comment()
    test_varproxy_set()
    test_varproxy_increment_decrement()
    test_varproxy_operators()
    test_js_helper()
    test_nested_if_in_while()
    test_full_example()
    test_bool_none()
    test_array_dict()
    test_varproxy_prop_idx_call()

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)
