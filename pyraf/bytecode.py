from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, List, Optional, Tuple


class Op(Enum):
    # stack / constants
    CONST = auto()       # push constant index
    POP = auto()         # pop top

    # variables
    LOAD = auto()        # push value of name-constant
    STORE = auto()       # store top into name-constant (does not pop by default in our VM)
    SET = auto()         # set existing name (like STORE but errors if missing) - optional

    # unary / binary
    NEG = auto()
    NOT = auto()

    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()

    EQ = auto()
    NEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()

    AND = auto()
    OR = auto()

    # control flow
    JUMP = auto()        # relative jump
    JUMP_IF_FALSE = auto()
    JUMP_IF_TRUE = auto()

    # calls
    CALL = auto()        # call with argc
    RET = auto()         # return top (or None if stack empty)

    # containers
    BUILD_LIST = auto()  # argc items -> list
    INDEX = auto()       # a[b]

    # functions
    MAKE_FUNC = auto()   # create function object from code constant


@dataclass(frozen=True)
class Instr:
    op: Op
    a: Optional[int] = None
    b: Optional[int] = None
    # source position for debugging (line, col)
    line: int = 0
    col: int = 0


@dataclass
class Chunk:
    name: str = "<module>"
    consts: List[Any] = None
    code: List[Instr] = None

    def __post_init__(self):
        if self.consts is None:
            self.consts = []
        if self.code is None:
            self.code = []

    def add_const(self, value: Any) -> int:
        self.consts.append(value)
        return len(self.consts) - 1

    def emit(self, op: Op, a: int | None = None, b: int | None = None, line: int = 0, col: int = 0) -> int:
        self.code.append(Instr(op=op, a=a, b=b, line=line, col=col))
        return len(self.code) - 1

    def patch_arg(self, ip: int, *, a: int | None = None, b: int | None = None) -> None:
        ins = self.code[ip]
        self.code[ip] = Instr(op=ins.op, a=a if a is not None else ins.a, b=b if b is not None else ins.b, line=ins.line, col=ins.col)


def disassemble(chunk: Chunk) -> str:
    out: List[str] = []
    out.append(f"== {chunk.name} ==")
    out.append("Constants:")
    for i, c in enumerate(chunk.consts):
        out.append(f"  [{i:03d}] {repr(c)}")
    out.append("Code:")
    for ip, ins in enumerate(chunk.code):
        a = "" if ins.a is None else str(ins.a)
        b = "" if ins.b is None else str(ins.b)
        loc = f"{ins.line}:{ins.col}" if ins.line or ins.col else "-"
        if ins.a is None and ins.b is None:
            out.append(f"{ip:04d}  {loc:>6}  {ins.op.name}")
        elif ins.b is None:
            out.append(f"{ip:04d}  {loc:>6}  {ins.op.name:<14} {a}")
        else:
            out.append(f"{ip:04d}  {loc:>6}  {ins.op.name:<14} {a} {b}")
    return "\n".join(out)