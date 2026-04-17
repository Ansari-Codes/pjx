"""
Comprehensive test suite for PJx — NEW FEATURES.
Tests: Switch, Class, Destructuring, Spread, Obj, Optional Chaining,
       Nullish Coalescing, Modules, Tagged Templates, Generators, Private Fields.
"""
from pjx import *


# ===================================================================
# Switch / Case / Default
# ===================================================================

def test_switch_basic():
    JavaScript.reset()
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

    output = JavaScript.to_string().strip()
    assert 'switch (day) {' in output
    assert 'case "Monday":' in output
    assert 'console.log("Start of week");' in output
    assert 'break;' in output
    assert 'default:' in output
    assert 'console.log("Midweek");' in output
    print("  PASS: Switch/Case/Default")


def test_switch_multiple_cases():
    JavaScript.reset()
    x = Let("x", 5)
    with Switch(x):
        with Case("1"):
            Print("one")
            Break()
        with Case("5"):
            Print("five")
            Break()

    output = JavaScript.to_string().strip()
    assert 'switch (x) {' in output
    assert 'case 1:' in output
    assert 'case 5:' in output
    print("  PASS: Switch multiple cases")


# ===================================================================
# Classes
# ===================================================================

def test_class_basic():
    JavaScript.reset()
    with Class("Person"):
        with ClassConstructor("name", "age"):
            This("name").set(JS("name"))
            This("age").set(JS("age"))
        with ClassMethod("greet"):
            Print("Hello, ${this.name}")

    output = JavaScript.to_string().strip()
    assert 'class Person {' in output
    assert 'constructor(name, age) {' in output
    assert 'this.name = name;' in output
    assert 'this.age = age;' in output
    assert 'greet() {' in output
    print("  PASS: Class basic")


def test_class_extends():
    JavaScript.reset()
    with Class("Dog", extends="Animal"):
        with ClassConstructor("name"):
            Super("name")
            This("type").set(JS("'dog'"))
        with ClassMethod("bark"):
            Print("Woof!")

    output = JavaScript.to_string().strip()
    assert 'class Dog extends Animal {' in output
    assert 'super(name);' in output
    assert "this.type = 'dog';" in output
    print("  PASS: Class extends + super")


def test_class_getter_setter():
    JavaScript.reset()
    with Class("Circle"):
        with ClassConstructor("radius"):
            This("_radius").set(JS("radius"))
        with Getter("radius"):
            Return(This("_radius"))
        with Setter("radius", "value"):
            This("_radius").set(JS("value"))

    output = JavaScript.to_string().strip()
    assert 'get radius() {' in output
    assert 'set radius(value) {' in output
    assert 'return this._radius;' in output
    print("  PASS: Class getter/setter")


def test_class_static_method():
    JavaScript.reset()
    with Class("MathHelper"):
        with ClassStaticMethod("add", "a", "b"):
            Return(JS("a + b"))

    output = JavaScript.to_string().strip()
    assert 'static add(a, b) {' in output
    print("  PASS: Class static method")


def test_private_field():
    JavaScript.reset()
    PrivateField("#age", 0)
    assert JavaScript.to_string().strip() == "#age = 0;"

    JavaScript.reset()
    PrivateField("#name")
    assert JavaScript.to_string().strip() == "#name;"
    print("  PASS: PrivateField")


def test_static_field():
    JavaScript.reset()
    StaticField("count", 0)
    assert JavaScript.to_string().strip() == "static count = 0;"

    JavaScript.reset()
    StaticField("#privateStatic", 42)
    assert JavaScript.to_string().strip() == "static #privateStatic = 42;"
    print("  PASS: StaticField")


def test_this_helper():
    JavaScript.reset()
    This("name").set(JS("'Alice'"))
    assert JavaScript.to_string().strip() == "this.name = 'Alice';"

    # This().call() returns an expression, not a statement
    expr = This().call("render")
    assert expr.expr == "this.render()"
    print("  PASS: This helper")


# ===================================================================
# Destructuring
# ===================================================================

def test_destruct_obj():
    JavaScript.reset()
    Const("props", DestructObj("name", "age"), JS("user"))
    output = JavaScript.to_string().strip()
    assert output == "const {name, age} = user;"
    print("  PASS: DestructObj")


def test_destruct_obj_alias():
    JavaScript.reset()
    Const("data", DestructObj("name", val="value"), JS("config"))
    output = JavaScript.to_string().strip()
    assert output == "const {name, value: val} = config;"
    print("  PASS: DestructObj with alias")


def test_destruct_arr():
    JavaScript.reset()
    Let("coords", DestructArr("x", "y"), JS("point"))
    output = JavaScript.to_string().strip()
    assert output == "let [x, y] = point;"
    print("  PASS: DestructArr")


def test_destruct_arr_rest():
    JavaScript.reset()
    Let("first", DestructArr("a", "...rest"), JS("items"))
    output = JavaScript.to_string().strip()
    assert output == "let [a, ...rest] = items;"
    print("  PASS: DestructArr with rest")


# ===================================================================
# Spread
# ===================================================================

def test_spread_in_array():
    JavaScript.reset()
    Let("arr", [1, 2, Spread(JS("more"))])
    output = JavaScript.to_string().strip()
    assert output == "let arr = [1, 2, ...more];"
    print("  PASS: Spread in array")


def test_spread_in_fncall():
    JavaScript.reset()
    FnCall("fn", 1, Spread(JS("args")), 2)
    output = JavaScript.to_string().strip()
    assert output == "fn(1, ...args, 2);"
    print("  PASS: Spread in FnCall")


# ===================================================================
# Object literals (Obj)
# ===================================================================

def test_obj_basic():
    JavaScript.reset()
    Let("data", Obj(x=1, y=2))
    output = JavaScript.to_string().strip()
    assert output == "let data = {x: 1, y: 2};"
    print("  PASS: Obj basic")


def test_obj_shorthand():
    JavaScript.reset()
    name = Let("name", JS("'Alice'"))
    age = Let("age", 30)
    # When key matches VarProxy name, use shorthand
    Let("person", Obj(name=name, age=age))
    output = JavaScript.to_string().strip()
    assert "let person = {name, age};" in output
    print("  PASS: Obj shorthand")


def test_obj_computed_key():
    JavaScript.reset()
    Let("dyn", Obj(computed={"[keyVar]": 42}))
    output = JavaScript.to_string().strip()
    assert output == "let dyn = {[keyVar]: 42};"
    print("  PASS: Obj computed key")


def test_obj_spread():
    JavaScript.reset()
    Let("merged", Obj(spreads=[JS("defaults")], x=1))
    output = JavaScript.to_string().strip()
    assert output == "let merged = {...defaults, x: 1};"
    print("  PASS: Obj with spread")


def test_obj_getter_setter():
    JavaScript.reset()
    Let("config", Obj(getters={"version": JS("'1.0'")}, setters={"value": "v"}))
    output = JavaScript.to_string().strip()
    assert "get version() { return '1.0'; }" in output
    assert "set value(v) { }" in output
    print("  PASS: Obj getter/setter")


def test_obj_method():
    JavaScript.reset()
    Let("obj", Obj(methods={"greet": "name"}))
    output = JavaScript.to_string().strip()
    assert "greet(name) { }" in output
    print("  PASS: Obj method syntax")


# ===================================================================
# Optional Chaining (?.)
# ===================================================================

def test_optchain_varproxy():
    JavaScript.reset()
    user = Let("user", JS("{}"))
    expr = user.optchain("name")
    assert expr.expr == "user?.name"
    print("  PASS: VarProxy.optchain")


def test_optchain_standalone():
    JavaScript.reset()
    Let("name", OptChain(JS("user"), "name"))
    output = JavaScript.to_string().strip()
    assert output == "let name = user?.name;"
    print("  PASS: OptChain standalone")


def test_optidx():
    JavaScript.reset()
    Let("first", OptIdx(JS("items"), 0))
    output = JavaScript.to_string().strip()
    assert output == "let first = items?.[0];"
    print("  PASS: OptIdx")


def test_optcall():
    JavaScript.reset()
    user = Let("user", JS("{}"))
    expr = user.optcall("toString")
    assert expr.expr == "user?.toString()"
    print("  PASS: VarProxy.optcall")


def test_optchain_jsexpr():
    JavaScript.reset()
    expr = JS("user.address").optchain("street")
    assert expr.expr == "user.address?.street"
    print("  PASS: _JSExpr.optchain")


# ===================================================================
# Nullish Coalescing (??)
# ===================================================================

def test_nullish_varproxy():
    JavaScript.reset()
    x = Let("x", JS("undefined"))
    expr = x.Nullish(0)
    assert expr.expr == "x ?? 0"
    print("  PASS: VarProxy.Nullish")


def test_nullish_standalone():
    JavaScript.reset()
    Let("val", Nullish(JS("input"), 0))
    output = JavaScript.to_string().strip()
    assert output == "let val = input ?? 0;"
    print("  PASS: Nullish standalone")


def test_nullish_jsexpr():
    JavaScript.reset()
    expr = JS("config.timeout").Nullish(3000)
    assert expr.expr == "config.timeout ?? 3000"
    print("  PASS: _JSExpr.Nullish")


# ===================================================================
# Modules (import / export)
# ===================================================================

def test_import_named():
    JavaScript.reset()
    Import("lodash", "debounce", "throttle")
    output = JavaScript.to_string().strip()
    assert output == 'import {debounce, throttle} from "lodash";'
    print("  PASS: Import named")


def test_import_default():
    JavaScript.reset()
    Import("react", default="React")
    output = JavaScript.to_string().strip()
    assert output == 'import React from "react";'
    print("  PASS: Import default")


def test_import_default_named():
    JavaScript.reset()
    Import("react", "useState", "useEffect", default="React")
    output = JavaScript.to_string().strip()
    assert output == 'import React, {useState, useEffect} from "react";'
    print("  PASS: Import default + named")


def test_import_namespace():
    JavaScript.reset()
    Import("lodash", module_alias="_")
    output = JavaScript.to_string().strip()
    assert output == 'import * as _ from "lodash";'
    print("  PASS: Import namespace")


def test_import_side_effect():
    JavaScript.reset()
    Import("./side-effects.js")
    output = JavaScript.to_string().strip()
    assert output == 'import "./side-effects.js";'
    print("  PASS: Import side-effect")


def test_import_dynamic():
    JavaScript.reset()
    Let("mod", Await(ImportDynamic("./myModule.js")))
    output = JavaScript.to_string().strip()
    assert output == 'let mod = await import("./myModule.js");'
    print("  PASS: ImportDynamic")


def test_export_named():
    JavaScript.reset()
    Export("add", "subtract")
    output = JavaScript.to_string().strip()
    assert output == "export {add, subtract};"
    print("  PASS: Export named")


def test_export_default_name():
    JavaScript.reset()
    ExportDefault("MyClass")
    output = JavaScript.to_string().strip()
    assert output == "export default MyClass;"
    print("  PASS: ExportDefault name")


def test_export_default_expr():
    JavaScript.reset()
    ExportDefault(expr=JS("{ foo: 1 }"))
    output = JavaScript.to_string().strip()
    assert output == "export default { foo: 1 };"
    print("  PASS: ExportDefault expression")


# ===================================================================
# Tagged Template Literals
# ===================================================================

def test_tagged_template():
    JavaScript.reset()
    Let("result", TaggedTemplate("html", "<div>${content}</div>"))
    output = JavaScript.to_string().strip()
    assert output == "let result = html`<div>${content}</div>`;"
    print("  PASS: TaggedTemplate")


def test_tagged_template_css():
    JavaScript.reset()
    Let("styled", TaggedTemplate("css", "color: ${color};"))
    output = JavaScript.to_string().strip()
    assert output == "let styled = css`color: ${color};`;"
    print("  PASS: TaggedTemplate CSS")


# ===================================================================
# Generators
# ===================================================================

def test_generator_func():
    JavaScript.reset()
    with GeneratorFunc("range", "start", "end"):
        i = Let("i", JS("start"))
        with While(i < JS("end")):
            Yield(i)
            i.set(i + 1)

    output = JavaScript.to_string().strip()
    assert 'function* range(start, end) {' in output
    assert 'yield i;' in output
    print("  PASS: GeneratorFunc")


def test_yield_no_value():
    JavaScript.reset()
    Yield()
    assert JavaScript.to_string().strip() == "yield;"
    print("  PASS: Yield no value")


def test_yield_from():
    JavaScript.reset()
    YieldFrom(JS("anotherGenerator()"))
    output = JavaScript.to_string().strip()
    assert output == "yield* anotherGenerator();"
    print("  PASS: YieldFrom")


# ===================================================================
# Combined / Integration tests
# ===================================================================

def test_class_with_private_fields():
    JavaScript.reset()
    with Class("BankAccount"):
        PrivateField("#balance", 0)
        with ClassConstructor("initialBalance"):
            This("#balance").set(JS("initialBalance"))
        with Getter("balance"):
            Return(This("#balance"))
        with ClassMethod("deposit", "amount"):
            This("#balance").set(This("#balance") + JS("amount"))

    output = JavaScript.to_string().strip()
    assert 'class BankAccount {' in output
    assert '#balance = 0;' in output
    assert 'this.#balance = initialBalance;' in output
    assert 'get balance() {' in output
    assert 'return this.#balance;' in output
    assert 'deposit(amount) {' in output
    assert 'this.#balance = this.#balance + amount;' in output
    print("  PASS: Class with private fields integration")


def test_full_class_inheritance():
    JavaScript.reset()
    with Class("Student", extends="Person"):
        with ClassConstructor("name", "grade"):
            Super("name")
            This("grade").set(JS("grade"))
        with ClassMethod("introduce"):
            Print("I'm ${this.name} in grade ${this.grade}")
        with ClassStaticMethod("create", "name", "grade"):
            Return(New("Student", JS("name"), JS("grade")))

    output = JavaScript.to_string().strip()
    assert 'class Student extends Person {' in output
    assert 'constructor(name, grade) {' in output
    assert 'super(name);' in output
    assert 'introduce() {' in output
    assert 'static create(name, grade) {' in output
    assert 'return new Student(name, grade);' in output
    print("  PASS: Full class inheritance")


def test_switch_fallthrough():
    JavaScript.reset()
    x = Let("x", 3)
    with Switch(x):
        with Case("1"):
            pass  # fallthrough
        with Case("2"):
            pass  # fallthrough
        with Case("3"):
            Print("small")
            Break()
        with Default():
            Print("big")

    output = JavaScript.to_string().strip()
    assert 'case 1:' in output
    assert 'case 2:' in output
    assert 'case 3:' in output
    assert 'console.log("small");' in output
    print("  PASS: Switch fallthrough")


def test_obj_mixed_features():
    JavaScript.reset()
    Let("config", Obj(
        spreads=[JS("defaults")],
        x=1,
        computed={"[dynamicKey]": 42},
        methods={"render": "props"},
    ))
    output = JavaScript.to_string().strip()
    assert "...defaults" in output
    assert "x: 1" in output
    assert "[dynamicKey]: 42" in output
    assert "render(props) { }" in output
    print("  PASS: Obj mixed features")


def test_destructuring_in_function():
    JavaScript.reset()
    with Func("handleUser", "user"):
        Const("props", DestructObj("name", "age"), JS("user"))
        Const("coords", DestructArr("x", "y"), JS("user.position"))
        Print("Name: ${name}, Age: ${age}")

    output = JavaScript.to_string().strip()
    assert 'const {name, age} = user;' in output
    assert 'const [x, y] = user.position;' in output
    print("  PASS: Destructuring in function")


if __name__ == "__main__":
    print("=" * 60)
    print("PJx NEW FEATURES Test Suite")
    print("=" * 60)

    # Switch
    test_switch_basic()
    test_switch_multiple_cases()

    # Classes
    test_class_basic()
    test_class_extends()
    test_class_getter_setter()
    test_class_static_method()

    # Private / Static fields
    test_private_field()
    test_static_field()
    test_this_helper()

    # Destructuring
    test_destruct_obj()
    test_destruct_obj_alias()
    test_destruct_arr()
    test_destruct_arr_rest()

    # Spread
    test_spread_in_array()
    test_spread_in_fncall()

    # Obj
    test_obj_basic()
    test_obj_shorthand()
    test_obj_computed_key()
    test_obj_spread()
    test_obj_getter_setter()
    test_obj_method()

    # Optional Chaining
    test_optchain_varproxy()
    test_optchain_standalone()
    test_optidx()
    test_optcall()
    test_optchain_jsexpr()

    # Nullish Coalescing
    test_nullish_varproxy()
    test_nullish_standalone()
    test_nullish_jsexpr()

    # Modules
    test_import_named()
    test_import_default()
    test_import_default_named()
    test_import_namespace()
    test_import_side_effect()
    test_import_dynamic()
    test_export_named()
    test_export_default_name()
    test_export_default_expr()

    # Tagged Templates
    test_tagged_template()
    test_tagged_template_css()

    # Generators
    test_generator_func()
    test_yield_no_value()
    test_yield_from()

    # Integration
    test_class_with_private_fields()
    test_full_class_inheritance()
    test_switch_fallthrough()
    test_obj_mixed_features()
    test_destructuring_in_function()

    print("\n" + "=" * 60)
    print("ALL NEW FEATURE TESTS PASSED!")
    print("=" * 60)
