![Banner](/static/banner.png)

> **P**ython **J**avaScript e**x**change — Use Python syntax to programmatically generate JavaScript code.

PJx is a Python library that lets you write JavaScript using Python's own syntax. Through the magic of context managers, operator overloading, and a smart variable proxy system, your Python code **is** your JavaScript code. No templates, no string concatenation headaches — just clean, idiomatic Python that emits clean, idiomatic JavaScript.

```python
from pjx import *

x = Let("x", 10)

with If(x > 10):
    Print("x is greater than 10 with value ${x}")
with Elif(x < 10):
    Print("Nope, it is smaller with the value of ${x}")
with Else():
    Print("Ah! It is equal to ${x}")

JavaScript.save_this_file("compiled.py.js")
```

**Output:**

```javascript
let x = 10;
if (x === 10) {
    console.log("Ah! It is equal to ${x}");
} else if (x < 10) {
    console.log("Nope, it is smaller with the value of ${x}");
} else {
    console.log("Ah! It is equal to ${x}");
}
```

---

## Table of Contents

- [PJx — Write JavaScript in Python](#pjx--write-javascript-in-python)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Core Concepts](#core-concepts)
    - [VarProxy — Smart Variable Wrappers](#varproxy--smart-variable-wrappers)
    - [JS() — Raw Expressions](#js--raw-expressions)
    - [Template Literals](#template-literals)
    - [Context Managers \& Indentation](#context-managers--indentation)
  - [Variable Declarations](#variable-declarations)
  - [Control Flow](#control-flow)
    - [If / Elif / Else](#if--elif--else)
    - [Switch / Case / Default](#switch--case--default)
    - [While](#while)
    - [For (Classic)](#for-classic)
    - [For...Of](#forof)
    - [For...In](#forin)
  - [Functions](#functions)
    - [Function Declaration](#function-declaration)
    - [Arrow Function](#arrow-function)
    - [Generator Functions](#generator-functions)
  - [Async / Await](#async--await)
    - [Async Function](#async-function)
    - [Async Arrow Function](#async-arrow-function)
    - [Await Expression](#await-expression)
    - [For Await...Of](#for-awaitof)
  - [Error Handling](#error-handling)
    - [Try / Catch / Finally](#try--catch--finally)
    - [Throw](#throw)
  - [Classes](#classes)
    - [Class Declaration](#class-declaration)
    - [Constructor](#constructor)
    - [Methods \& Static Methods](#methods--static-methods)
    - [Getters \& Setters](#getters--setters)
    - [Private Fields](#private-fields)
    - [Static Fields](#static-fields)
    - [This \& Super](#this--super)
    - [Full Class Example with Inheritance](#full-class-example-with-inheritance)
  - [Destructuring](#destructuring)
    - [Object Destructuring](#object-destructuring)
    - [Array Destructuring](#array-destructuring)
  - [Spread / Rest](#spread--rest)
  - [Object Literals](#object-literals)
  - [Optional Chaining \& Nullish Coalescing](#optional-chaining--nullish-coalescing)
  - [Modules (Import / Export)](#modules-import--export)
    - [Import](#import)
    - [Dynamic Import](#dynamic-import)
    - [Export](#export)
  - [Tagged Template Literals](#tagged-template-literals)
  - [Utility Statements](#utility-statements)
    - [Print](#print)
    - [FnCall](#fncall)
    - [New](#new)
    - [Return](#return)
    - [Break / Continue](#break--continue)
    - [Comment](#comment)
    - [Raw](#raw)
  - [Output Management](#output-management)
  - [Complete API Reference](#complete-api-reference)
  - [Design Philosophy](#design-philosophy)
  - [License](#license)
- [👨‍💻 About me:](#-about-me)
- [This project was vibecoded with GLM-4.7!](#this-project-was-vibecoded-with-glm-47)

---

## Installation

Clone the repository and add it to your Python path:

```bash
git clone https://github.com/your-repo/pjx.git
cd pjx
```

Then import in your project:

```python
from pjx import *
```

PJx has **zero dependencies** — it only uses Python's standard library.

---

## Quick Start

```python
from pjx import *

# Declare variables
name = Const("name", "PJx")
version = Let("version", "1.0.0")

# Write a function
with Func("greet", "name"):
    Print("Hello, ${name}!")
    Return(JS("name"))

# Call it
FnCall("greet", "World")

# Save the generated JavaScript
JavaScript.save_this_file("output.js")
```

**Generated `output.js`:**

```javascript
const name = "PJx";
let version = "1.0.0";
function greet(name) {
    console.log(`Hello, ${name}!`);
    return name;
}
greet("World");
```

---

## Core Concepts

### VarProxy — Smart Variable Wrappers

When you call `Let()`, `Const()`, or `Var()`, you get back a `VarProxy` object. This is the heart of PJx — it overloads Python operators so that expressions like `x > 10` or `y + 1` produce **JavaScript expression strings** instead of evaluating in Python.

```python
x = Let("x", 10)

# These produce JavaScript expressions, NOT Python booleans/ints:
x > 10        # -> JSExpr("x > 10")
x + 5         # -> JSExpr("x + 5")
x == 0        # -> JSExpr("x === 0")  (=== for strict equality)
x * 2 + 1     # -> JSExpr("(x * 2) + 1")
```

**Supported operators on VarProxy:**

| Python Syntax | JavaScript Output | Category |
|---|---|---|
| `x + y` | `x + y` | Arithmetic |
| `x - y` | `x - y` | Arithmetic |
| `x * y` | `x * y` | Arithmetic |
| `x / y` | `x / y` | Arithmetic |
| `x // y` | `Math.floor(x / y)` | Arithmetic (floor div) |
| `x % y` | `x % y` | Arithmetic |
| `x ** y` | `Math.pow(x, y)` | Arithmetic |
| `x == y` | `x === y` | Comparison (strict) |
| `x != y` | `x !== y` | Comparison (strict) |
| `x < y`, `x <= y`, `x > y`, `x >= y` | Same | Comparison |
| `x & y`, `x \| y`, `x ^ y` | Same | Bitwise |
| `x << y`, `x >> y` | Same | Bitwise shift |
| `~x` | `~x` | Bitwise NOT |
| `-x` | `-x` | Unary negation |

Since Python's `and`/`or`/`not` keywords cannot be overloaded, PJx provides method equivalents:

```python
x.And(y)     # -> x && y
x.Or(y)      # -> x || y
x.Not()      # -> !x
```

**Property and method access:**

```python
x.prop("length")          # -> x.length
x.idx(0)                  # -> x[0]
x.call("push", 1, 2)     # -> x.push(1, 2)
x.set(42)                 # -> x = 42;  (emits assignment statement)
x.increment()             # -> x++;
x.decrement()             # -> x--;
```

### JS() — Raw Expressions

Sometimes you need to pass a raw JavaScript expression that should **not** be quoted as a string. The `JS()` wrapper tells PJx to emit the content verbatim:

```python
Return(JS("name"))              # -> return name;     (not return "name";)
Return(JS("a + b"))             # -> return a + b;
Let("data", JS("fetch(url)"))   # -> let data = fetch(url);
FnCall("console.log", JS("x"))  # -> console.log(x);
```

Without `JS()`, strings are automatically quoted as JavaScript string literals:

```python
Let("greeting", "hello")        # -> let greeting = "hello";
Print("value is ${x}")          # -> console.log(`value is ${x}`);
```

### Template Literals

Strings containing `${...}` are automatically converted to JavaScript template literals (backtick strings). Regular strings use double quotes:

```python
Print("Hello, ${name}!")    # -> console.log(`Hello, ${name}!`);
Print("Hello, World!")      # -> console.log("Hello, World!");
```

This works everywhere strings are used — in `Let`, `Print`, `Return`, `FnCall`, etc.

### Context Managers & Indentation

PJx uses Python's `with` statement (context managers) to represent JavaScript blocks. Indentation is handled automatically — you never need to manage braces or spacing:

```python
with Func("calculate", "a", "b"):
    result = Let("result", JS("a * b + a"))
    with If(result > 100):
        Print("Big result: ${result}")
    with Else():
        Print("Small result: ${result}")
    Return(result)
```

The closing braces are managed intelligently — for `if/elif/else` chains, the closing brace is deferred until we know whether another branch follows, producing clean `} else if` and `} else` output.

---

## Variable Declarations

PJx supports all three JavaScript variable declaration keywords:

```python
# let
x = Let("x", 10)       # -> let x = 10;
y = Let("y")            # -> let y;

# const
PI = Const("PI", 3.14)  # -> const PI = 3.14;

# var (legacy)
count = Var("count", 0)  # -> var count = 0;
```

All three return a `VarProxy` that can be used in subsequent expressions.

**Type mapping:**

| Python Value | JavaScript Output |
|---|---|
| `10` (int) | `10` |
| `3.14` (float) | `3.14` |
| `"hello"` (str) | `"hello"` |
| `"val is ${x}"` (str with `${}`) | `` `val is ${x}` `` |
| `True` / `False` | `true` / `false` |
| `None` | `null` |
| `[1, 2, 3]` (list) | `[1, 2, 3]` |
| `{"a": 1}` (dict) | `{a: 1}` |

---

## Control Flow

### If / Elif / Else

```python
score = Let("score", 85)

with If(score >= 90):
    Print("Grade: A")
with Elif(score >= 80):
    Print("Grade: B")
with Elif(score >= 70):
    Print("Grade: C")
with Else():
    Print("Grade: F")
```

**Output:**

```javascript
let score = 85;
if (score >= 90) {
    console.log("Grade: A");
} else if (score >= 80) {
    console.log("Grade: B");
} else if (score >= 70) {
    console.log("Grade: C");
} else {
    console.log("Grade: F");
}
```

### Switch / Case / Default

```python
action = Let("action", JS("'FETCH_START'"))

with Switch(action):
    with Case("'FETCH_START'"):
        Print("Loading started")
        Break()
    with Case("'FETCH_SUCCESS'"):
        Print("Data loaded")
        Break()
    with Case("'FETCH_ERROR'"):
        Print("Error occurred")
        Break()
    with Default():
        Print("Unknown action")
```

**Output:**

```javascript
let action = 'FETCH_START';
switch (action) {
    case 'FETCH_START':
        console.log("Loading started");
        break;
    case 'FETCH_SUCCESS':
        console.log("Data loaded");
        break;
    case 'FETCH_ERROR':
        console.log("Error occurred");
        break;
    default:
        console.log("Unknown action");
}
```

> **Note:** `Case` values are emitted as raw JS — use `JS()` for expressions or provide the exact string you want (including quotes for string literals).

### While

```python
count = Let("count", 0)

with While(count < 10):
    Print("count = ${count}")
    count.increment()
```

**Output:**

```javascript
let count = 0;
while (count < 10) {
    console.log(`count = ${count}`);
    count++;
}
```

### For (Classic)

Classic C-style `for` loops. All three arguments are emitted as raw JavaScript:

```python
with For("let i = 0", "i < 10", "i++"):
    Print("i = ${i}")
```

**Output:**

```javascript
for (let i = 0; i < 10; i++) {
    console.log(`i = ${i}`);
}
```

### For...Of

Iterate over iterables:

```python
fruits = Let("fruits", ["apple", "banana", "cherry"])

with ForOf("fruit", fruits):
    Print("Fruit: ${fruit}")
```

**Output:**

```javascript
let fruits = ["apple", "banana", "cherry"];
for (let fruit of fruits) {
    console.log(`Fruit: ${fruit}`);
}
```

### For...In

Iterate over object keys:

```python
person = Let("person", {"name": "Alice", "age": 30})

with ForIn("key", person):
    Print("key = ${key}")
```

**Output:**

```javascript
let person = {name: "Alice", age: 30};
for (let key in person) {
    console.log(`key = ${key}`);
}
```

---

## Functions

### Function Declaration

```python
with Func("greet", "name", "greeting"):
    Print("${greeting}, ${name}!")
    Return(JS("name"))
```

**Output:**

```javascript
function greet(name, greeting) {
    console.log(`${greeting}, ${name}!`);
    return name;
}
```

### Arrow Function

Arrow functions are declared as `const` assignments:

```python
with ArrowFunc("add", "a", "b"):
    Return(JS("a + b"))
```

**Output:**

```javascript
const add = (a, b) => {
    return a + b;
};
```

### Generator Functions

```python
with GeneratorFunc("fibonacci"):
    a = Let("a", 0)
    b = Let("b", 1)
    with While(True):
        Yield(a)
        temp = Let("temp", a + b)
        a.set(b)
        b.set(temp)
```

**Output:**

```javascript
function* fibonacci() {
    let a = 0;
    let b = 1;
    while (true) {
        yield a;
        let temp = a + b;
        a = b;
        b = temp;
    }
}
```

**`Yield` and `YieldFrom`:**

```python
Yield(JS("value"))                 # -> yield value;
Yield()                            # -> yield;
YieldFrom(JS("anotherGenerator()"))  # -> yield* anotherGenerator();
```

---

## Async / Await

PJx fully supports JavaScript's async/await syntax. Async context managers also implement `__aenter__`/`__aexit__`, so you can use them with `async with` in Python as well.

### Async Function

```python
with AsyncFunc("fetchData", "url"):
    data = Let("data", Await(JS("fetch(url)")))
    Return(data)
```

**Output:**

```javascript
async function fetchData(url) {
    let data = await fetch(url);
    return data;
}
```

### Async Arrow Function

```python
with AsyncArrowFunc("debouncedSearch", "query"):
    result = Let("result", Await(JS("searchAPI(query)")))
    Return(result)
```

**Output:**

```javascript
const debouncedSearch = async (query) => {
    let result = await searchAPI(query);
    return result;
};
```

### Await Expression

`Await()` can be used inline in variable declarations and return statements, or as a standalone statement:

```python
# Inline
response = Let("response", Await(JS("fetch(url)")))

# Standalone statement
Await(JS("initializeApp()")).emit()

# Inside Python async function (uses __await__)
# await Await(JS("someAsync()"))
```

### For Await...Of

Async iteration over streams:

```python
stream = Let("stream", JS("getReadableStream()"))

with ForAwait("chunk", stream):
    Print("Received chunk: ${chunk}")
```

**Output:**

```javascript
let stream = getReadableStream();
for await (let chunk of stream) {
    console.log(`Received chunk: ${chunk}`);
}
```

---

## Error Handling

### Try / Catch / Finally

```python
with Try():
    response = Let("response", Await(JS("fetch(url)")))
    data = Let("data", Await(response.call("json")))
    Return(data)
with Catch("error"):
    Print("Failed: ${error}")
    Throw(New("Error", "Fetch failed"))
with Finally():
    Print("Request completed")
```

**Output:**

```javascript
try {
    let response = await fetch(url);
    let data = await response.json();
    return data;
} catch (error) {
    console.log(`Failed: ${error}`);
    throw new Error("Fetch failed");
} finally {
    console.log("Request completed");
}
```

### Throw

```python
Throw(JS("new Error('something went wrong')"))
Throw(New("TypeError", "Invalid argument"))
```

---

## Classes

PJx provides comprehensive support for ES6+ class syntax, including inheritance, private fields, static members, getters, and setters.

### Class Declaration

```python
with Class("Animal"):
    with ClassConstructor("name", "sound"):
        This("name").set(JS("name"))
        This("sound").set(JS("sound"))

    with ClassMethod("speak"):
        Print("${this.name} says ${this.sound}")
```

**Output:**

```javascript
class Animal {
    constructor(name, sound) {
        this.name = name;
        this.sound = sound;
    }
    speak() {
        console.log(`${this.name} says ${this.sound}`);
    }
}
```

### Constructor

Use `ClassConstructor` inside a `Class` block:

```python
with ClassConstructor("name", "age"):
    Super()                       # -> super();
    This("name").set(JS("name"))  # -> this.name = name;
    This("age").set(JS("age"))    # -> this.age = age;
```

### Methods & Static Methods

```python
with ClassMethod("greet"):                    # -> greet() {
    Print("Hello!")                           # ->     console.log("Hello!");
                                              # -> }

with ClassStaticMethod("create", "name"):     # -> static create(name) {
    Return(New("User", JS("name")))           # ->     return new User(name);
                                              # -> }
```

### Getters & Setters

```python
with Getter("fullName"):                                    # -> get fullName() {
    Return(JS("this.firstName + ' ' + this.lastName"))      # ->     return this.firstName + ' ' + this.lastName;
                                                             # -> }

with Setter("email", "newEmail"):                           # -> set email(newEmail) {
    with If(JS("newEmail.includes('@')")):                  # ->     if (newEmail.includes('@')) {
        This("_email").set(JS("newEmail"))                  # ->         this._email = newEmail;
                                                             # ->     }
                                                             # -> }
```

### Private Fields

JavaScript private fields using the `#` prefix:

```python
PrivateField("#age", 0)      # -> #age = 0;
PrivateField("#name")         # -> #name;
```

### Static Fields

```python
StaticField("count", 0)          # -> static count = 0;
StaticField("#privateStatic", 42) # -> static #privateStatic = 42;
```

### This & Super

```python
This("name").set(JS("name"))   # -> this.name = name;
This().call("emit", JS("'login'"))  # -> this.emit('login');

Super()                         # -> super();
Super(JS("name"))               # -> super(name);
```

### Full Class Example with Inheritance

```python
with Class("User", extends="EventEmitter"):
    PrivateField("#email")

    with ClassConstructor("name", "email"):
        Super()
        This("name").set(JS("name"))
        This("#email").set(JS("email"))
        This("loggedIn").set(False)

    with Getter("email"):
        Return(This("#email"))

    with Setter("email", "newEmail"):
        with If(JS("newEmail.includes('@')")):
            This("#email").set(JS("newEmail"))

    with ClassMethod("login", "password"):
        with If(JS("password === this.#password")):
            This("loggedIn").set(True)
            This().call("emit", JS("'login'"), This("name"))
            Return(True)
        Return(False)

    with ClassStaticMethod("create", "data"):
        Return(New("User", JS("data.name"), JS("data.email")))
```

---

## Destructuring

### Object Destructuring

```python
# Basic
Const("props", DestructObj("name", "age"), JS("user"))
# -> const {name, age} = user;

# With alias (rename)
Const("data", DestructObj("name", val="value"), JS("response"))
# -> const {name, value: val} = response;
```

### Array Destructuring

```python
# Basic
Let("coords", DestructArr("x", "y"), JS("point"))
# -> let [x, y] = point;

# With rest element
Let("first", DestructArr("a", "...rest"), JS("items"))
# -> let [a, ...rest] = items;
```

Destructuring works with all three declaration keywords (`Let`, `Const`, `Var`). The pattern is always: `Declaration(name, pattern, source)`.

---

## Spread / Rest

The `Spread()` wrapper produces the JavaScript `...` operator:

```python
# Spread in arrays
Let("merged", [1, 2, Spread(JS("moreItems"))])
# -> let merged = [1, 2, ...moreItems];

# Spread in function calls
FnCall("callback", Spread(JS("args")))
# -> callback(...args);

# Spread in objects (via Obj)
Let("combined", Obj(spreads=[JS("defaults")], extra=True))
# -> let combined = {...defaults, extra: true};
```

---

## Object Literals

The `Obj` builder supports all JavaScript object literal features:

```python
# Regular key-value pairs
Let("config", Obj(timeout=5000, retries=3))
# -> let config = {timeout: 5000, retries: 3};

# Shorthand (when key matches VarProxy name)
name = Let("name", JS("'Alice'"))
Let("user", Obj(name=name))
# -> let user = {name};  (shorthand!)

# Computed keys
Let("dyn", Obj(computed={"[keyVar]": 42}))
# -> let dyn = {[keyVar]: 42};

# Spread entries
Let("merged", Obj(spreads=[JS("defaults"), JS("overrides")], x=1))
# -> let merged = {...defaults, ...overrides, x: 1};

# Method syntax
Let("obj", Obj(methods={"greet": "name"}))
# -> let obj = {greet(name) { }};

# Getter / Setter
Let("obj", Obj(getters={"area": "this.w * this.h"}, setters={"width": "val"}))
# -> let obj = {get area() { return this.w * this.h; }, set width(val) { }};
```

---

## Optional Chaining & Nullish Coalescing

PJx supports modern JavaScript's safe navigation operators through both methods on `VarProxy`/`_JSExpr` and standalone helper functions.

**Method-based (on VarProxy and _JSExpr):**

```python
user = Let("user", JS("fetchUser()"))

user.optchain("name")              # -> user?.name
user.optchain("address").optchain("city")  # -> user?.address?.city
user.optidx(0)                     # -> user?.[0]
user.optcall("toString")           # -> user?.toString()
user.Nullish("Anonymous")          # -> user ?? "Anonymous"
```

**Function-based (for arbitrary expressions):**

```python
Let("city", OptChain(JS("user"), "address"))
# -> let city = user?.address;

Let("firstItem", OptIdx(JS("items"), 0))
# -> let firstItem = items?.[0];

Let("name", Nullish(JS("user.name"), JS("'Anonymous'")))
# -> let name = user.name ?? 'Anonymous';
```

**Chaining optional operators:**

```python
Let("city", OptChain(JS("user"), "address").optchain("city"))
# -> let city = user?.address?.city;
```

---

## Modules (Import / Export)

PJx supports all JavaScript `import` and `export` forms.

### Import

```python
# Named imports
Import("lodash", "debounce", "throttle")
# -> import {debounce, throttle} from "lodash";

# Default import
Import("react", default="React")
# -> import React from "react";

# Default + named
Import("react", "useState", "useEffect", default="React")
# -> import React, {useState, useEffect} from "react";

# Namespace import
Import("lodash", module_alias="_")
# -> import * as _ from "lodash";

# Side-effect import
Import("./side-effects.js")
# -> import "./side-effects.js";
```

### Dynamic Import

```python
Let("mod", Await(ImportDynamic("./myModule.js")))
# -> let mod = await import("./myModule.js");
```

### Export

```python
# Named export
Export("add", "subtract")
# -> export {add, subtract};

# Default export
ExportDefault("MyClass")
# -> export default MyClass;

# Default export with expression
ExportDefault(expr=JS("{ foo: 1 }"))
# -> export default { foo: 1 };
```

---

## Tagged Template Literals

```python
Let("result", TaggedTemplate("html", "<div class='${cls}'>${content}</div>"))
# -> let result = html`<div class='${cls}'>${content}</div>`;

Let("styled", TaggedTemplate("css", "color: ${color}; font-size: ${size}px;"))
# -> let styled = css`color: ${color}; font-size: ${size}px;`;

Let("query", TaggedTemplate("sql", "SELECT * FROM ${table} WHERE ${condition}"))
# -> let query = sql`SELECT * FROM ${table} WHERE ${condition}`;
```

---

## Utility Statements

### Print

Emits `console.log()`. Automatically handles template literals:

```python
Print("Hello, ${name}!")        # -> console.log(`Hello, ${name}!`);
Print("Simple message")          # -> console.log("Simple message");
Print(JS("x"), JS("y"))         # -> console.log(x, y);
```

### FnCall

Call any JavaScript function:

```python
FnCall("alert", "Hello!")           # -> alert("Hello!");
FnCall("setTimeout", JS("callback"), 1000)  # -> setTimeout(callback, 1000);
```

### New

Create a `new` expression (returns `_JSExpr`, doesn't emit by itself):

```python
Let("user", New("User", JS("'Alice'")))
# -> let user = new User('Alice');

Return(New("Map"))
# -> return new Map();
```

### Return

```python
Return(JS("value"))    # -> return value;
Return(42)             # -> return 42;
Return()               # -> return;
```

### Break / Continue

```python
Break()      # -> break;
Continue()   # -> continue;
```

### Comment

```python
Comment("This is a note")   # -> // This is a note
```

### Raw

Inject raw JavaScript code directly:

```python
Raw("const PI = Math.PI;")
Raw("console.log(PI);")
Raw("""if (complex) {
    doSomething();
}""")
```

---

## Output Management

The `JavaScript` class provides static methods for managing the generated code:

```python
# Save to file
JavaScript.save_this_file("output.js")

# Get as string
js_code = JavaScript.to_string()
print(js_code)

# Reset the buffer (start fresh)
JavaScript.reset()

# Add a blank line
JavaScript.add_blank()
```

---

## Complete API Reference

| API | Type | JavaScript Output |
|---|---|---|
| `Let(name, value)` | Function | `let name = value;` |
| `Const(name, value)` | Function | `const name = value;` |
| `Var(name, value)` | Function | `var name = value;` |
| `If(condition)` | Context Manager | `if (condition) { ... }` |
| `Elif(condition)` | Context Manager | `} else if (condition) { ... }` |
| `Else()` | Context Manager | `} else { ... }` |
| `Switch(expr)` | Context Manager | `switch (expr) { ... }` |
| `Case(value)` | Context Manager | `case value:` |
| `Default()` | Context Manager | `default:` |
| `While(condition)` | Context Manager | `while (condition) { ... }` |
| `For(init, cond, update)` | Context Manager | `for (init; cond; update) { ... }` |
| `ForOf(var, iterable)` | Context Manager | `for (let var of iterable) { ... }` |
| `ForIn(var, obj)` | Context Manager | `for (let var in obj) { ... }` |
| `Func(name, *params)` | Context Manager | `function name(params) { ... }` |
| `ArrowFunc(name, *params)` | Context Manager | `const name = (params) => { ... };` |
| `AsyncFunc(name, *params)` | Context Manager | `async function name(params) { ... }` |
| `AsyncArrowFunc(name, *params)` | Context Manager | `const name = async (params) => { ... };` |
| `Await(expr)` | Expression | `await expr` |
| `ForAwait(var, iterable)` | Context Manager | `for await (let var of iterable) { ... }` |
| `Try()` | Context Manager | `try { ... }` |
| `Catch(var)` | Context Manager | `} catch (var) { ... }` |
| `Finally()` | Context Manager | `} finally { ... }` |
| `Throw(value)` | Statement | `throw value;` |
| `Class(name, extends)` | Context Manager | `class name [extends X] { ... }` |
| `ClassConstructor(*params)` | Context Manager | `constructor(params) { ... }` |
| `ClassMethod(name, *params)` | Context Manager | `name(params) { ... }` |
| `ClassStaticMethod(name, *params)` | Context Manager | `static name(params) { ... }` |
| `Getter(name)` | Context Manager | `get name() { ... }` |
| `Setter(name, param)` | Context Manager | `set name(param) { ... }` |
| `This(attr)` | Function | `this` or `this.attr` (returns VarProxy) |
| `Super(*args)` | Statement | `super(args);` |
| `PrivateField(name, value)` | Statement | `#name = value;` |
| `StaticField(name, value)` | Statement | `static name = value;` |
| `DestructObj(*names, **aliases)` | Expression | `{names, aliases}` |
| `DestructArr(*names)` | Expression | `[names]` |
| `Spread(expr)` | Expression | `...expr` |
| `Obj(**kv, shorthand, computed, methods, spreads, getters, setters)` | Expression | `{ ... }` |
| `ObjMethod(name, *params)` | Expression | `name(params)` |
| `OptChain(expr, attr)` | Function | `expr?.attr` |
| `OptIdx(expr, index)` | Function | `expr?.[index]` |
| `Nullish(expr, default)` | Function | `expr ?? default` |
| `Import(module, *names, default, module_alias)` | Statement | `import ... from "module";` |
| `ImportDynamic(module)` | Expression | `import("module")` |
| `Export(*names)` | Statement | `export {names};` |
| `ExportDefault(name)` | Statement | `export default name;` |
| `TaggedTemplate(tag, *parts)` | Expression | `` tag`parts` `` |
| `GeneratorFunc(name, *params)` | Context Manager | `function* name(params) { ... }` |
| `Yield(value)` | Statement | `yield value;` |
| `YieldFrom(iterable)` | Statement | `yield* iterable;` |
| `Return(value)` | Statement | `return value;` |
| `Print(*values)` | Statement | `console.log(values);` |
| `FnCall(name, *args)` | Statement | `name(args);` |
| `New(class_name, *args)` | Expression | `new ClassName(args)` |
| `Break()` | Statement | `break;` |
| `Continue()` | Statement | `continue;` |
| `Comment(text)` | Statement | `// text` |
| `Raw(js)` | Statement | *(raw JS, emitted as-is)* |
| `JS(expr)` | Expression | *(raw JS expression, unquoted)* |
| `JavaScript.save_this_file(path)` | Static Method | *(writes buffer to file)* |
| `JavaScript.to_string()` | Static Method | *(returns buffer as string)* |
| `JavaScript.reset()` | Static Method | *(clears the buffer)* |
| `JavaScript.add_blank()` | Static Method | *(inserts blank line)* |

---

## Design Philosophy

PJx is built on four core principles:

1. **Python is the DSL.** There is no custom template language or AST manipulation layer. You write Python, and Python's own syntax does the heavy lifting. Context managers handle blocks, operator overloading handles expressions, and function calls handle statements.

2. **Zero mental overhead.** The mapping from PJx API to JavaScript output should be obvious and predictable. `Let("x", 10)` produces `let x = 10;`. `with If(x > 10):` produces `if (x > 10) {`. What you write is what you get.

3. **Global accumulator.** All PJx constructs append to a single global code buffer. There is no manual state management — you just call functions and enter context managers, and the output assembles itself. This makes PJx code read top-to-bottom exactly like the JavaScript it produces.

4. **Progressive disclosure.** The basic API (`Let`, `If`, `Func`, `Print`) covers 80% of use cases. Advanced features (classes, destructuring, generators, optional chaining) are available when you need them but don't clutter the simple case.

---

## License

Apache

---

# 👨‍💻 About me:
I am Muhammad Abubakar Siddique Ansari, a 1st-year ICS student at KIPS College, Punjab (Pakistan). I'm passionate about Data Science, AI, and building tools that make developers' lives easier.

Portfolio: [ansari-codes.github.io/portfolio](ansari-codes.github.io/portfolio)

# This project was vibecoded with GLM-4.7!

# LOGO/TRADEMARK
![logo](/static/logo.svg)

