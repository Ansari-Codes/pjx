from pjx import *

x = Let("x", 10)

JavaScript.add_blank()

with If(x > 10):
    Print("x is greater than 10 with value ${x}.")
with Elif(x < 10):
    Print("Nope, it is smaller with the value of ${x}.")
with Else():
    Print("Ah! It is equal to ${x}.")

JavaScript.add_blank()

y = Let("y", 0)

JavaScript.add_blank()

with While(y < 10):
    y.set(y + 1)

JavaScript.add_blank()

Print("Final value of y is ${y}.")

JavaScript.save_this_file("compiled.js")

print("=== Generated JavaScript ===")
print(JavaScript.to_string())
