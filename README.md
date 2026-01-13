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

---

## Quickstart

### Run a file (AST interpreter)
```bash
python -m pyraf.cli run examples/demo.raf
