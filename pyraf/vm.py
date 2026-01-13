from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .bytecode import Chunk, Instr, Op
from .errors import RuntimeError_, format_error
from .runtime import Env, ReturnSignal


@dataclass
class VMFunction:
    chunk: Chunk
    params: List[str]
    closure: Env
    name: str


@dataclass
class Frame:
    func: VMFunction
    ip: int
    env: Env


class VM:
    def __init__(self, src: str):
        self.src = src
        self.stack: List[Any] = []
        self.globals = Env()
        self.frames: List[Frame] = []
        self._install_builtins()

    def _install_builtins(self) -> None:
        def b_print(args: List[Any]) -> Any:
            print(*args)
            return None

        def b_len(args: List[Any]) -> Any:
            if len(args) != 1:
                raise RuntimeError_("len() expects exactly 1 argument")
            return len(args[0])

        self.globals.define("print", ("builtin", b_print))
        self.globals.define("len", ("builtin", b_len))

    def _runtime_err(self, ins: Instr, msg: str) -> RuntimeError_:
        if ins.line or ins.col:
            return RuntimeError_(format_error(self.src, ins.line, ins.col, msg))
        return RuntimeError_(msg)

    def run(self, chunk: Chunk) -> Any:
        # module function wrapper (no params)
        main = VMFunction(chunk=chunk, params=[], closure=self.globals, name=chunk.name)
        frame = Frame(func=main, ip=0, env=Env(self.globals))
        self.frames = [frame]
        self.stack = []

        while self.frames:
            f = self.frames[-1]
            if f.ip >= len(f.func.chunk.code):
                # no more instructions -> return None
                self.frames.pop()
                if not self.frames:
                    return None
                self.stack.append(None)
                continue

            ins = f.func.chunk.code[f.ip]
            f.ip += 1

            try:
                self._step(ins, f)
            except RuntimeError_ as e:
                raise self._runtime_err(ins, str(e)) from None

        return None

    def _pop(self) -> Any:
        if not self.stack:
            raise RuntimeError_("Stack underflow")
        return self.stack.pop()

    def _peek(self) -> Any:
        if not self.stack:
            raise RuntimeError_("Stack underflow")
        return self.stack[-1]

    def _step(self, ins: Instr, f: Frame) -> None:
        op = ins.op

        if op == Op.CONST:
            self.stack.append(f.func.chunk.consts[ins.a])
            return

        if op == Op.POP:
            _ = self._pop()
            return

        if op == Op.LOAD:
            name = f.func.chunk.consts[ins.a]
            self.stack.append(f.env.get(name))
            return

        if op == Op.STORE:
            name = f.func.chunk.consts[ins.a]
            val = self._peek()
            # update if exists in parent chain; else define local
            try:
                f.env.set(name, val)
            except RuntimeError_:
                f.env.define(name, val)
            return

        if op == Op.NEG:
            v = self._pop()
            self.stack.append(-v)
            return

        if op == Op.NOT:
            v = self._pop()
            self.stack.append(not bool(v))
            return

        if op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD,
                  Op.EQ, Op.NEQ, Op.LT, Op.LTE, Op.GT, Op.GTE):
            b = self._pop()
            a = self._pop()
            if op == Op.ADD: self.stack.append(a + b); return
            if op == Op.SUB: self.stack.append(a - b); return
            if op == Op.MUL: self.stack.append(a * b); return
            if op == Op.DIV: self.stack.append(a / b); return
            if op == Op.MOD: self.stack.append(a % b); return

            if op == Op.EQ: self.stack.append(a == b); return
            if op == Op.NEQ: self.stack.append(a != b); return
            if op == Op.LT: self.stack.append(a < b); return
            if op == Op.LTE: self.stack.append(a <= b); return
            if op == Op.GT: self.stack.append(a > b); return
            if op == Op.GTE: self.stack.append(a >= b); return

        if op == Op.JUMP:
            f.ip += ins.a
            return

        if op == Op.JUMP_IF_FALSE:
            v = self._peek()
            if not bool(v):
                f.ip += ins.a
            return

        if op == Op.JUMP_IF_TRUE:
            v = self._peek()
            if bool(v):
                f.ip += ins.a
            return

        if op == Op.BUILD_LIST:
            n = ins.a or 0
            if n:
                items = self.stack[-n:]
                del self.stack[-n:]
            else:
                items = []
            self.stack.append(list(items))
            return

        if op == Op.INDEX:
            idx = self._pop()
            target = self._pop()
            if not isinstance(idx, int):
                raise RuntimeError_("Index must be an integer")
            self.stack.append(target[idx])
            return

        if op == Op.MAKE_FUNC:
            proto = f.func.chunk.consts[ins.a]
            fn_chunk, params = proto
            fn = VMFunction(chunk=fn_chunk, params=params, closure=f.env, name=fn_chunk.name)
            self.stack.append(fn)
            return

        if op == Op.CALL:
            argc = ins.a or 0
            # stack: [..., callee, arg1, arg2, ...]
            args = []
            for _ in range(argc):
                args.append(self._pop())
            args.reverse()
            callee = self._pop()

            # builtins are stored as ("builtin", fn)
            if isinstance(callee, tuple) and callee[0] == "builtin":
                res = callee[1](args)
                self.stack.append(res)
                return

            if isinstance(callee, VMFunction):
                if len(args) != len(callee.params):
                    raise RuntimeError_(f"Function expected {len(callee.params)} args, got {len(args)}")

                new_env = Env(callee.closure)
                for p, a in zip(callee.params, args):
                    new_env.define(p, a)

                self.frames.append(Frame(func=callee, ip=0, env=new_env))
                return

            raise RuntimeError_("Can only call functions")

        if op == Op.RET:
            ret = self._pop() if self.stack else None
            self.frames.pop()
            if not self.frames:
                # end of module
                self.stack.append(ret)
                return
            # return to caller
            self.stack.append(ret)
            return

        raise RuntimeError_(f"Unknown opcode: {op.name}")