from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional
from .tokens import Token

# --------------------
# Expressions
# --------------------
class Expr:
    pass

@dataclass(frozen=True)
class Number(Expr):
    value: int | float
    tok: Token

@dataclass(frozen=True)
class String(Expr):
    value: str
    tok: Token

@dataclass(frozen=True)
class Bool(Expr):
    value: bool
    tok: Token

@dataclass(frozen=True)
class NoneLit(Expr):
    tok: Token

@dataclass(frozen=True)
class Var(Expr):
    name: str
    tok: Token

@dataclass(frozen=True)
class Unary(Expr):
    op: Token
    right: Expr

@dataclass(frozen=True)
class Binary(Expr):
    left: Expr
    op: Token
    right: Expr

@dataclass(frozen=True)
class Call(Expr):
    callee: Expr
    lparen: Token
    args: List[Expr]

# (Optional later) list literals + indexing:
@dataclass(frozen=True)
class ListLit(Expr):
    lbracket: Token
    items: List[Expr]

@dataclass(frozen=True)
class Index(Expr):
    target: Expr
    lbracket: Token
    index: Expr

# --------------------
# Statements
# --------------------
class Stmt:
    pass

@dataclass(frozen=True)
class ExprStmt(Stmt):
    expr: Expr

@dataclass(frozen=True)
class Assign(Stmt):
    name: Token   # IDENT token
    value: Expr

@dataclass(frozen=True)
class Import(Stmt):
    path_tok: Token   # STRING token
    path: str         # string literal contents

@dataclass(frozen=True)
class Block(Stmt):
    lbrace: Token
    statements: List[Stmt]

@dataclass(frozen=True)
class If(Stmt):
    if_tok: Token
    cond: Expr
    then_branch: Block
    else_branch: Optional[Block]

@dataclass(frozen=True)
class While(Stmt):
    while_tok: Token
    cond: Expr
    body: Block

@dataclass(frozen=True)
class Return(Stmt):
    return_tok: Token
    value: Optional[Expr]

@dataclass(frozen=True)
class Def(Stmt):
    def_tok: Token
    name: Token        # IDENT token
    params: List[Token]  # IDENT tokens
    body: Block
