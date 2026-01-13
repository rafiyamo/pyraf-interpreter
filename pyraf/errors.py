from __future__ import annotations

class PyRafError(Exception):
    pass

class LexError(PyRafError):
    pass

class ParseError(PyRafError):
    pass

class RuntimeError_(PyRafError):
    pass

def format_error(src: str, line: int, col: int, msg: str) -> str:
    lines = src.splitlines()
    snippet = lines[line - 1] if 1 <= line <= len(lines) else ""
    caret = " " * (max(col, 1) - 1) + "^"
    return f"[line {line}, col {col}] {msg}\n{snippet}\n{caret}"
