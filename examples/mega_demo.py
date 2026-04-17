"""
PJx Mega Demo — showcases ALL features of the PJx library.

This demo generates a complete JavaScript application using Python syntax.
Run: python mega_demo.py
Output: mega_demo_output.js
"""
from pjx import *

# ===================================================================
# 1. MODULE IMPORTS
# ===================================================================

Import("react", "useState", "useEffect", default="React")
Import("lodash", "debounce", "throttle")
Import("lodash", module_alias="_")
Import("./styles.css")

JavaScript.add_blank()

# ===================================================================
# 2. CONSTANTS & DESTRUCTURING
# ===================================================================

Const("API_URL", JS("'https://api.example.com'"))
Const("CONFIG", Obj(
    spreads=[JS("defaultConfig")],
    timeout=5000,
    retries=3,
    computed={"[envKey]": JS("'production'")},
))

JavaScript.add_blank()

# Object destructuring
Const("props", DestructObj("name", "age", "email"), JS("userData"))
# Array destructuring with rest
Let("first", DestructArr("head", "...tail"), JS("items"))
# Destructuring with alias
Const("data", DestructObj("name", val="value"), JS("response"))

JavaScript.add_blank()

# ===================================================================
# 3. SPREAD / REST
# ===================================================================

Let("merged", [1, 2, Spread(JS("moreItems"))])
Let("combined", Obj(spreads=[JS("defaults"), JS("overrides")], extra=True))

JavaScript.add_blank()

# ===================================================================
# 4. OPTIONAL CHAINING & NULLISH COALESCING
# ===================================================================

user = Let("user", JS("fetchUser()"))

Let("city", OptChain(JS("user"), "address").optchain("city"))
Let("firstItem", OptIdx(JS("items"), 0))
Let("name", Nullish(JS("user.name"), JS("'Anonymous'")))
Let("timeout", JS("config.timeout").Nullish(3000))

JavaScript.add_blank()

# ===================================================================
# 5. SWITCH STATEMENT
# ===================================================================

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

JavaScript.add_blank()

# ===================================================================
# 6. OBJECT LITERALS (shorthand, computed, methods)
# ===================================================================

status = Let("status", JS("'active'"))
id_val = Let("id", 42)

Let("query", Obj(
    spreads=[JS("baseQuery")],
    status=status,    # shorthand since key matches VarProxy name
    id=id_val,        # shorthand
    computed={"[sortKey]": JS("'asc'")},
    methods={"toString": ""},
))

JavaScript.add_blank()

# ===================================================================
# 7. TAGGED TEMPLATE LITERALS
# ===================================================================

Let("html", TaggedTemplate("html", "<div class='${cls}'>${content}</div>"))
Let("css", TaggedTemplate("css", "body { color: ${color}; font-size: ${size}px; }"))
Let("sql", TaggedTemplate("sql", "SELECT * FROM ${table} WHERE ${condition}"))

JavaScript.add_blank()

# ===================================================================
# 8. GENERATOR FUNCTION
# ===================================================================

with GeneratorFunc("fibonacci"):
    a = Let("a", 0)
    b = Let("b", 1)
    with While(True):
        Yield(a)
        temp = Let("temp", a + b)
        a.set(b)
        b.set(temp)

JavaScript.add_blank()

with GeneratorFunc("take", "n"):
    with ForOf("item", JS("iterable")):
        with If(JS("n--") <= 0):
            Return()
        Yield(JS("item"))

JavaScript.add_blank()

# ===================================================================
# 9. CLASS WITH FULL FEATURES
# ===================================================================

with Class("EventEmitter"):
    Comment("Simple event emitter")
    PrivateField("#listeners")
    StaticField("eventCount", 0)

    with ClassConstructor():
        This("#listeners").set(Obj())

    with ClassMethod("on", "event", "callback"):
        Raw("if (!this.#listeners[event]) this.#listeners[event] = [];")
        Raw("this.#listeners[event].push(callback);")
        Return(This())

    with ClassMethod("emit", "event", "...args"):
        Raw("const listeners = this.#listeners[event];")
        with If(JS("listeners")):
            with ForOf("cb", JS("listeners")):
                FnCall("cb", Spread(JS("args")))
        Raw("EventEmitter.eventCount++;")

    with Getter("listenerCount"):
        Return(JS("Object.keys(this.#listeners).length"))

JavaScript.add_blank()

# ===================================================================
# 10. CLASS WITH INHERITANCE
# ===================================================================

with Class("User", extends="EventEmitter"):
    PrivateField("#email")
    PrivateField("#password")

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

JavaScript.add_blank()

# ===================================================================
# 11. ASYNC PATTERNS (Try/Catch/Finally + Async)
# ===================================================================

with AsyncFunc("fetchUserData", "userId"):
    with Try():
        response = Let("response", Await(JS("fetch(`${API_URL}/users/${userId}`)")))
        data = Let("data", Await(response.call("json")))
        Return(data)
    with Catch("error"):
        Print("Failed to fetch user: ${error}")
        Throw(New("Error", "User fetch failed"))
    with Finally():
        Print("Fetch attempt completed")

JavaScript.add_blank()

with AsyncArrowFunc("debouncedSearch", "query"):
    result = Let("result", Await(JS("searchAPI(query)")))
    Return(result)

JavaScript.add_blank()

# ===================================================================
# 12. EXPORTS
# ===================================================================

Export("User", "fetchUserData", "fibonacci")
ExportDefault("User")

# ===================================================================
# SAVE
# ===================================================================

JavaScript.save_this_file("mega_demo_output.js")
print("✅ Mega demo generated: mega_demo_output.js")
