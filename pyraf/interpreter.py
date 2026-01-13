from __future__ import annotations

from typing import Any, List, Tuple

from . import ast as A
from pathlib import Path
from .errors import RuntimeError_, format_error
from .runtime import Env, Function, ReturnSignal

class Interpreter:
    def __init__(self, src: str, base_dir: str | None = None):
        self.src = src
        self.base_dir = base_dir 
        self.globals = Env()
        self._install_builtins()

        # Call stack frames: (function_name, line, col)
        self._frames: List[Tuple[str, int, int]] = []
        self._imported: set[str] = set()


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

    def _format_stacktrace(self) -> str:
        if not self._frames:
            return ""
        lines = ["Stack trace (most recent call last):"]
        for name, line, col in reversed(self._frames):
            lines.append(f"  at {name} (line {line}, col {col})")
        return "\n".join(lines)

    def run(self, program: List[A.Stmt]) -> None:
        for s in program:
            self.exec_stmt(s, self.globals)

    # for REPL: execute in a persistent environment
    def run_in_env(self, program: List[A.Stmt], env: Env) -> None:
        for s in program:
            self.exec_stmt(s, env)

    def truthy(self, v: Any) -> bool:
        return bool(v)
    
    def _resolve_import_path(self, path: str) -> str:
        import os
        if os.path.isabs(path):
            return path
        base = self.base_dir or os.getcwd()
        return os.path.normpath(os.path.join(base, path))


    # -------------------------
    # Statements
    # -------------------------
    def exec_block(self, block: A.Block, env: Env) -> None:
        for s in block.statements:
            self.exec_stmt(s, env)

    def exec_stmt(self, stmt: A.Stmt, env: Env) -> None:
        try:
            if isinstance(stmt, A.ExprStmt):
                _ = self.eval_expr(stmt.expr, env)
                return

            if isinstance(stmt, A.Assign):
                name = stmt.name.lexeme
                val = self.eval_expr(stmt.value, env)
                # update existing binding in any enclosing scope; otherwise define locally
                try:
                    env.set(name, val)
                except RuntimeError_:
                    env.define(name, val)
                return
            
            if isinstance(stmt, A.Import):
                import os
                from pyraf.lexer import lex
                from pyraf.parser import Parser

                full_path = self._resolve_import_path(stmt.path)

                if full_path in self._imported:
                    return  # cached

                if not os.path.exists(full_path):
                    raise RuntimeError_(f"Import not found: {stmt.path}")

                mod_src = Path(full_path).read_text(encoding="utf-8")
                self._imported.add(full_path)

                # Run module in the *same* env so its defs become available
                prev_src = self.src
                prev_base = self.base_dir
                try:
                    self.src = mod_src
                    self.base_dir = os.path.dirname(full_path)
                    tokens = lex(mod_src)
                    program = Parser(tokens, mod_src).parse_program()
                    for s2 in program:
                        self.exec_stmt(s2, env)
                finally:
                    self.src = prev_src
                    self.base_dir = prev_base
                return


            if isinstance(stmt, A.Block):
                # new lexical scope
                self.exec_block(stmt, Env(env))
                return

            if isinstance(stmt, A.If):
                cond = self.eval_expr(stmt.cond, env)
                if self.truthy(cond):
                    self.exec_block(stmt.then_branch, Env(env))
                elif stmt.else_branch is not None:
                    self.exec_block(stmt.else_branch, Env(env))
                return

            if isinstance(stmt, A.While):
                while self.truthy(self.eval_expr(stmt.cond, env)):
                    self.exec_block(stmt.body, Env(env))
                return

            if isinstance(stmt, A.Def):
                fn = Function(
                    name=stmt.name.lexeme,
                    params=[p.lexeme for p in stmt.params],
                    body=stmt.body,
                    closure=env,
                )
                env.define(stmt.name.lexeme, fn)
                return

            if isinstance(stmt, A.Return):
                val = None if stmt.value is None else self.eval_expr(stmt.value, env)
                raise ReturnSignal(val)

            raise RuntimeError_("Unknown statement type")

        except RuntimeError_ as e:
            # try to locate a token for caret formatting
            tok = getattr(stmt, "if_tok", None) or getattr(stmt, "while_tok", None) or getattr(stmt, "return_tok", None)

            if tok is None and hasattr(stmt, "name"):
                maybe_tok = getattr(stmt, "name")
                if hasattr(maybe_tok, "line") and hasattr(maybe_tok, "col"):
                    tok = maybe_tok

            if tok is not None:
                base = format_error(self.src, tok.line, tok.col, str(e))
                st = self._format_stacktrace()
                if st:
                    base += "\n" + st
                raise RuntimeError_(base) from None

            # no token: still add stack trace if we have one
            msg = str(e)
            st = self._format_stacktrace()
            if st:
                msg += "\n" + st
            raise RuntimeError_(msg) from None

    # -------------------------
    # Expressions
    # -------------------------
    def eval_expr(self, expr: A.Expr, env: Env) -> Any:
        try:
            if isinstance(expr, A.Number):
                return expr.value
            if isinstance(expr, A.String):
                return expr.value
            if isinstance(expr, A.Bool):
                return expr.value
            if isinstance(expr, A.NoneLit):
                return None
            if isinstance(expr, A.Var):
                return env.get(expr.name)

            if isinstance(expr, A.ListLit):
                return [self.eval_expr(e, env) for e in expr.items]

            if isinstance(expr, A.Index):
                target = self.eval_expr(expr.target, env)
                idx = self.eval_expr(expr.index, env)
                if not isinstance(idx, int):
                    raise RuntimeError_("Index must be an integer")
                return target[idx]

            if isinstance(expr, A.Unary):
                right = self.eval_expr(expr.right, env)
                k = expr.op.kind.name
                if k == "MINUS":
                    return -right
                if k == "NOT":
                    return not self.truthy(right)
                raise RuntimeError_(f"Unknown unary operator {expr.op.lexeme}")

            if isinstance(expr, A.Binary):
                k = expr.op.kind.name

                # short-circuit
                if k == "AND":
                    left = self.eval_expr(expr.left, env)
                    return self.eval_expr(expr.right, env) if self.truthy(left) else left
                if k == "OR":
                    left = self.eval_expr(expr.left, env)
                    return left if self.truthy(left) else self.eval_expr(expr.right, env)

                left = self.eval_expr(expr.left, env)
                right = self.eval_expr(expr.right, env)

                if k == "PLUS": return left + right
                if k == "MINUS": return left - right
                if k == "STAR": return left * right
                if k == "SLASH": return left / right
                if k == "PERCENT": return left % right

                if k == "EQEQ": return left == right
                if k == "NEQ": return left != right
                if k == "LT": return left < right
                if k == "LTE": return left <= right
                if k == "GT": return left > right
                if k == "GTE": return left >= right

                raise RuntimeError_(f"Unknown operator {expr.op.lexeme}")

            if isinstance(expr, A.Call):
                callee = self.eval_expr(expr.callee, env)
                args = [self.eval_expr(a, env) for a in expr.args]

                # builtins
                if isinstance(callee, tuple) and callee[0] == "builtin":
                    return callee[1](args)

                # user function
                if isinstance(callee, Function):
                    callsite = expr.lparen
                    self._frames.append((callee.name, callsite.line, callsite.col))
                    try:
                        return callee.call(self, args)
                    finally:
                        self._frames.pop()

                raise RuntimeError_("Can only call functions")

            raise RuntimeError_("Unknown expression type")

        except RuntimeError_ as e:
            tok = getattr(expr, "tok", None) or getattr(expr, "lparen", None) or getattr(expr, "lbracket", None)
            if tok is not None:
                base = format_error(self.src, tok.line, tok.col, str(e))
                st = self._format_stacktrace()
                if st:
                    base += "\n" + st
                raise RuntimeError_(base) from None

            msg = str(e)
            st = self._format_stacktrace()
            if st:
                msg += "\n" + st
            raise RuntimeError_(msg) from None
