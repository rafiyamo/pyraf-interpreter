# PyRaf

PyRaf is a Python-inspired interpreted language implemented in Python. It includes a complete language pipeline — **lexer → Pratt parser → AST → interpreter** — plus a **bytecode compiler and stack-based VM** and a **disassembler**.

---

## Features

- **Lexer** with line/column tracking, strings, numbers, keywords, and `//` comments
- **Pratt parser** (expression precedence) producing an AST
- **AST interpreter** with:
  - lexical scoping and block environments
  - `if/else`, `while`
  - user-defined functions + `return`
  - **closures / nested functions**
  - runtime error formatting + **stack traces**
- **Bytecode compiler** (AST → bytecode)
- **Stack-based VM runtime** (bytecode execution)
- **Disassembler** (`pyraf dis`) to inspect emitted bytecode
- **Tests + CI**: unit tests for lexer/parser/evaluator and VM tests
- **Imports/modules**: import "path/file.raf"; with caching
- **Bytecode tooling**: dis command and stack-based VM execution (run --vm)
- **Diagnostics**: runtime errors include source context and call stack traces

---

## Quickstart

### Run a file (AST interpreter)
```bash
python -m pyraf.cli run examples/demo.raf
````

### Run a file (bytecode VM)

```bash
python -m pyraf.cli run --vm examples/demo.raf
```

### Disassemble to bytecode

```bash
python -m pyraf.cli dis examples/demo.raf
```

### Start the REPL

```bash
python -m pyraf.cli repl
```

---

## Language overview

### Statements

**Assignment**

```raf
x = 3;
```

**If / else**

```raf
if (x >= 10) { print("ok"); } else { print("no"); }
```

**While**

```raf
i = 0;
while (i < 3) {
  print(i);
  i = i + 1;
}
```

**Functions + return**

```raf
def add(a, b) { return a + b; }
print(add(2, 5));
```

**Closures / nested functions**

```raf
def make_adder(x) {
  def add(y) { return x + y; }
  return add;
}

add5 = make_adder(5);
print(add5(3)); // 8
```

### Imports (modules)

```raf
import "lib/math.raf";
print(square(9));
```

### Expressions

* Arithmetic: `+  -  *  /  %`
* Comparisons: `==  !=  <  <=  >  >=`
* Logical: `and  or  not` (short-circuiting in the compiler)
* Calls: `f(1, 2)`
* Lists + indexing: `[10, 20, 30]`, `lst[1]`

---

## Examples

* `examples/demo.raf` — assignments, arithmetic, and `if/else`
* `examples/closure.raf` — closures (nested function capturing outer variable)

Run:

```bash
python -m pyraf.cli run examples/closure.raf
python -m pyraf.cli run --vm examples/closure.raf
```

---

## Project structure

```text
pyraf/
  lexer.py        # source -> tokens
  tokens.py       # token definitions
  parser.py       # tokens -> AST (Pratt parser)
  ast.py          # AST node definitions
  runtime.py      # environments + function objects
  interpreter.py  # AST execution + stack traces
  bytecode.py     # instruction model + disassembler
  compiler.py     # AST -> bytecode
  vm.py           # stack-based bytecode VM
  cli.py          # command-line interface (run/dis/repl)

tests/
  test_lexer.py
  test_parser.py
  test_eval.py    # AST interpreter tests
  test_vm.py      # VM execution tests
```

---

## Running tests

```bash
python -m pytest
```

---

## Notes on design

* The AST interpreter is the reference execution model.
* The bytecode VM executes compiled code using a simple stack machine.
* Closures work by capturing the current lexical environment as a function’s closure.
* Runtime errors are formatted with source context and include a lightweight stack trace.
