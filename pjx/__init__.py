"""
PJx — Write Python which is JavaScript.

A Python API that lets you use Python syntax to generate JavaScript code.
Example:

    from pjx import *

    x = Let("x", 10)

    with If(x > 10):
        Print("x is greater than 10 with value ${x}")
    with Elif(x < 10):
        Print("Nope, it is smaller with the value of ${x}")
    with Else():
        Print("Ah! It is equal to ${x}")

    JavaScript.save_this_file("compiled.py.js")

Async example:

    with AsyncFunc("fetchUser", "id"):
        user = Let("user", Await(JS("db.find(id)")))
        Return(JS("user"))

Class example:

    with Class("Dog", extends="Animal"):
        with ClassConstructor("name"):
            Super("name")
            This("type").set("'dog'")
        with ClassMethod("bark"):
            Print("Woof!")

Destructuring example:

    Const("props", DestructObj("name", "age"), JS("user"))
    Let("first", DestructArr("x", "y"), JS("point"))
"""

from pjx.core import (
    VarProxy,
    Let,
    Const,
    Var,
    If,
    Elif,
    Else,
    While,
    For,
    ForOf,
    ForIn,
    Func,
    ArrowFunc,
    AsyncFunc,
    AsyncArrowFunc,
    Await,
    ForAwait,
    Try,
    Catch,
    Finally,
    Throw,
    New,
    Return,
    Print,
    FnCall,
    Raw,
    JS,
    JavaScript,
    Break,
    Continue,
    Comment,
    # Switch / Case / Default
    Switch,
    Case,
    Default,
    # Classes
    Class,
    ClassConstructor,
    ClassMethod,
    ClassStaticMethod,
    Getter,
    Setter,
    This,
    Super,
    PrivateField,
    StaticField,
    # Destructuring
    DestructObj,
    DestructArr,
    # Spread
    Spread,
    # Object literals
    Obj,
    ObjMethod,
    # Optional chaining / nullish coalescing
    OptChain,
    OptIdx,
    Nullish,
    # Modules
    Import,
    ImportDynamic,
    Export,
    ExportDefault,
    # Tagged templates
    TaggedTemplate,
    # Generators
    GeneratorFunc,
    Yield,
    YieldFrom,
)

__all__ = [
    "VarProxy",
    "Let",
    "Const",
    "Var",
    "If",
    "Elif",
    "Else",
    "While",
    "For",
    "ForOf",
    "ForIn",
    "Func",
    "ArrowFunc",
    "AsyncFunc",
    "AsyncArrowFunc",
    "Await",
    "ForAwait",
    "Try",
    "Catch",
    "Finally",
    "Throw",
    "New",
    "Return",
    "Print",
    "FnCall",
    "Raw",
    "JS",
    "JavaScript",
    "Break",
    "Continue",
    "Comment",
    # Switch
    "Switch",
    "Case",
    "Default",
    # Classes
    "Class",
    "ClassConstructor",
    "ClassMethod",
    "ClassStaticMethod",
    "Getter",
    "Setter",
    "This",
    "Super",
    "PrivateField",
    "StaticField",
    # Destructuring
    "DestructObj",
    "DestructArr",
    # Spread
    "Spread",
    # Object literals
    "Obj",
    "ObjMethod",
    # Optional chaining / nullish coalescing
    "OptChain",
    "OptIdx",
    "Nullish",
    # Modules
    "Import",
    "ImportDynamic",
    "Export",
    "ExportDefault",
    # Tagged templates
    "TaggedTemplate",
    # Generators
    "GeneratorFunc",
    "Yield",
    "YieldFrom",
]
