# PJx
> **->** *Write Python which is javascript*

This project aims to provide python api, in which we can use python syntax to generate javascript. For example:

```python
from pjx import *

x = Let("x", 10)

with If(x > 10):
    Print("x is greater than 10 with value ${x}")
with Elif(x < 10):
    Print("Nope, it is smaller with the value of ${x}")
with Else():
    Print("Ah! It is equal to ${x}")

y = Let("y", 0)

with While(y < 10):
    y.set(y + 1)

Print("Final value of y is ${y}.")

JavaScript.save_this_file("compiled.py.js")
```

## Expected JavaScript Output:
```javascript
let x = 10;

if (x > 10) {
    console.log(`x is greater than 10 with value ${x}.`);
} else if (x < 10) {
    console.log(`Nope, it is smaller with the value of ${x}.`);
} else {
    console.log(`Ah! It is equal to ${x}.`);
}

let y = 0;

while (y < 10) {
    y = y + 1;
}

console.log(`Final value of y is ${y}.`);
```

## How PJX Would Map Features:

| PJX Syntax |` JavaScript Output |
|------------|-------------------|
| `Let("x", 10)` | `let x = 10;` |
| `x = Let("x", 10)` | Returns a `VarProxy` that knows its name |
| `with If(x > 10):` | `if (x > 10) {` |
| `with Elif(x < 10):` | `} else if (x < 10) {` |
| `with Else():` | `} else {` |
| `Print("text ${x}")` | `console.log(`text ${x}`);` |
| `with While(y < 10):` | `while (y < 10) {` |
| `y.set(y + 1)` | `y = y + 1;` |
| `JavaScript.save_this_file()` | Writes the accumulated JS to file |

