from __future__ import annotations

from typing import List, Optional, Tuple

from . import ast as A
from .bytecode import Chunk, Op
from .errors import RuntimeError_


class Compiler:
    def __init__(self, src: str, name: str = "<module>"):
        self.src = src
        self.chunk = Chunk(name=name)

    # ---------- public ----------
    def compile_program(self, program: List[A.Stmt]) -> Chunk:
        for s in program:
            self.stmt(s)
        # implicit return at end of module
        self.chunk.emit(Op.CONST, self._k(None))
        self.chunk.emit(Op.RET)
        return self.chunk

    # ---------- helpers ----------
    def _k(self, value) -> int:
        return self.chunk.add_const(value)

    def _name(self, s: str) -> int:
        return self.chunk.add_const(s)

    def _emit_jump(self, op: Op, line: int = 0, col: int = 0) -> int:
        # placeholder offset in a, patch later
        return self.chunk.emit(op, a=0, line=line, col=col)

    def _patch_jump_to_here(self, ip: int) -> None:
        # Jumps are relative: offset = target_ip - (ip + 1)
        target = len(self.chunk.code)
        offset = target - (ip + 1)
        self.chunk.patch_arg(ip, a=offset)

    def _emit_loop(self, loop_start_ip: int, line: int = 0, col: int = 0) -> None:
        # Jump back: offset = loop_start - (current_ip + 1)
        cur = len(self.chunk.code)
        offset = loop_start_ip - (cur + 1)
        self.chunk.emit(Op.JUMP, a=offset, line=line, col=col)

    # ---------- statements ----------
    def stmt(self, s: A.Stmt) -> None:
        if isinstance(s, A.ExprStmt):
            self.expr(s.expr)
            self.chunk.emit(Op.POP)
            return

        if isinstance(s, A.Assign):
            self.expr(s.value)
            self.chunk.emit(Op.STORE, self._name(s.name.lexeme), line=s.name.line, col=s.name.col)
            return

        if isinstance(s, A.Block):
            for st in s.statements:
                self.stmt(st)
            return

        if isinstance(s, A.If):
            # cond
            self.expr(s.cond)
            j_if_false = self._emit_jump(Op.JUMP_IF_FALSE, line=s.if_tok.line, col=s.if_tok.col)

            # true path pops cond
            self.chunk.emit(Op.POP)
            self.stmt(s.then_branch)

            j_end = self._emit_jump(Op.JUMP, line=s.if_tok.line, col=s.if_tok.col)

            # else label: patch false jump to here
            self._patch_jump_to_here(j_if_false)

            # false path pops cond
            self.chunk.emit(Op.POP)

            if s.else_branch is not None:
                self.stmt(s.else_branch)

            self._patch_jump_to_here(j_end)
            return

        if isinstance(s, A.While):
            loop_start = len(self.chunk.code)

            # cond
            self.expr(s.cond)
            j_if_false = self._emit_jump(Op.JUMP_IF_FALSE, line=s.while_tok.line, col=s.while_tok.col)

            # true path pops cond
            self.chunk.emit(Op.POP)

            # body
            self.stmt(s.body)

            # jump back
            self._emit_loop(loop_start, line=s.while_tok.line, col=s.while_tok.col)

            # end label (false jump target)
            self._patch_jump_to_here(j_if_false)

            # false path pops cond
            self.chunk.emit(Op.POP)
            return

        if isinstance(s, A.Return):
            if s.value is None:
                self.chunk.emit(Op.CONST, self._k(None), line=s.return_tok.line, col=s.return_tok.col)
            else:
                self.expr(s.value)
            self.chunk.emit(Op.RET, line=s.return_tok.line, col=s.return_tok.col)
            return

        if isinstance(s, A.Def):
            # compile function body into its own chunk
            fn_name = s.name.lexeme
            params = [p.lexeme for p in s.params]

            fnc = Compiler(self.src, name=f"<fn {fn_name}>")
            # function body: compile statements
            for st in s.body.statements:
                fnc.stmt(st)
            # implicit return None if no explicit return
            fnc.chunk.emit(Op.CONST, fnc._k(None))
            fnc.chunk.emit(Op.RET)

            proto = (fnc.chunk, params)  # stored as constant
            proto_idx = self._k(proto)

            self.chunk.emit(Op.MAKE_FUNC, proto_idx, line=s.def_tok.line, col=s.def_tok.col)
            self.chunk.emit(Op.STORE, self._name(fn_name), line=s.name.line, col=s.name.col)
            return

        raise RuntimeError_(f"Compiler: unsupported statement {type(s).__name__}")

    # ---------- expressions ----------
    def expr(self, e: A.Expr) -> None:
        if isinstance(e, A.Number):
            self.chunk.emit(Op.CONST, self._k(e.value), line=e.tok.line, col=e.tok.col)
            return

        if isinstance(e, A.String):
            self.chunk.emit(Op.CONST, self._k(e.value), line=e.tok.line, col=e.tok.col)
            return

        if isinstance(e, A.Bool):
            self.chunk.emit(Op.CONST, self._k(e.value), line=e.tok.line, col=e.tok.col)
            return

        if isinstance(e, A.NoneLit):
            self.chunk.emit(Op.CONST, self._k(None), line=e.tok.line, col=e.tok.col)
            return

        if isinstance(e, A.Var):
            self.chunk.emit(Op.LOAD, self._name(e.name), line=e.tok.line, col=e.tok.col)
            return

        if isinstance(e, A.ListLit):
            for item in e.items:
                self.expr(item)
            self.chunk.emit(Op.BUILD_LIST, a=len(e.items), line=e.lbracket.line, col=e.lbracket.col)
            return

        if isinstance(e, A.Index):
            self.expr(e.target)
            self.expr(e.index)
            self.chunk.emit(Op.INDEX, line=e.lbracket.line, col=e.lbracket.col)
            return

        if isinstance(e, A.Unary):
            self.expr(e.right)
            k = e.op.kind.name
            if k == "MINUS":
                self.chunk.emit(Op.NEG, line=e.op.line, col=e.op.col)
                return
            if k == "NOT":
                self.chunk.emit(Op.NOT, line=e.op.line, col=e.op.col)
                return
            raise RuntimeError_(f"Compiler: unknown unary op {e.op.lexeme}")

        if isinstance(e, A.Binary):
            k = e.op.kind.name

            # short-circuit AND/OR
            if k == "AND":
                self.expr(e.left)
                j = self._emit_jump(Op.JUMP_IF_FALSE, line=e.op.line, col=e.op.col)
                self.chunk.emit(Op.POP)  # discard left (truthy), evaluate right
                self.expr(e.right)
                self._patch_jump_to_here(j)
                return

            if k == "OR":
                self.expr(e.left)
                j = self._emit_jump(Op.JUMP_IF_TRUE, line=e.op.line, col=e.op.col)
                self.chunk.emit(Op.POP)  # discard left (falsey), evaluate right
                self.expr(e.right)
                self._patch_jump_to_here(j)
                return

            # normal binary
            self.expr(e.left)
            self.expr(e.right)

            op_map = {
                "PLUS": Op.ADD,
                "MINUS": Op.SUB,
                "STAR": Op.MUL,
                "SLASH": Op.DIV,
                "PERCENT": Op.MOD,
                "EQEQ": Op.EQ,
                "NEQ": Op.NEQ,
                "LT": Op.LT,
                "LTE": Op.LTE,
                "GT": Op.GT,
                "GTE": Op.GTE,
            }
            if k not in op_map:
                raise RuntimeError_(f"Compiler: unknown binary op {e.op.lexeme}")

            self.chunk.emit(op_map[k], line=e.op.line, col=e.op.col)
            return

        if isinstance(e, A.Call):
            # callee then args then CALL argc
            self.expr(e.callee)
            for a in e.args:
                self.expr(a)
            self.chunk.emit(Op.CALL, a=len(e.args), line=e.lparen.line, col=e.lparen.col)
            return

        raise RuntimeError_(f"Compiler: unsupported expression {type(e).__name__}")


def compile_program(program: List[A.Stmt], src: str, name: str = "<module>") -> Chunk:
    return Compiler(src, name=name).compile_program(program)
