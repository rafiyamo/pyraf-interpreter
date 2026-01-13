from __future__ import annotations

from typing import List, Optional

from .tokens import Token, TokenKind
from .errors import ParseError, format_error
from . import ast as A


class Parser:
    def __init__(self, tokens: List[Token], src: str):
        self.toks = tokens
        self.src = src
        self.i = 0

    def peek(self) -> Token:
        return self.toks[self.i]

    def prev(self) -> Token:
        return self.toks[self.i - 1]

    def at_end(self) -> bool:
        return self.peek().kind == TokenKind.EOF

    def advance(self) -> Token:
        if not self.at_end():
            self.i += 1
        return self.prev()

    def check(self, kind: TokenKind) -> bool:
        return self.peek().kind == kind

    def match(self, *kinds: TokenKind) -> bool:
        if self.peek().kind in kinds:
            self.advance()
            return True
        return False

    def expect(self, kind: TokenKind, msg: str) -> Token:
        if self.check(kind):
            return self.advance()
        t = self.peek()
        raise ParseError(format_error(self.src, t.line, t.col, msg))

    # -------------------------
    # Program / statements
    # -------------------------
    def parse_program(self) -> List[A.Stmt]:
        stmts: List[A.Stmt] = []
        while not self.at_end():
            stmts.append(self.statement())
        return stmts

    def statement(self) -> A.Stmt:
        if self.match(TokenKind.IF):
            return self.if_stmt(self.prev())
        if self.match(TokenKind.WHILE):
            return self.while_stmt(self.prev())
        if self.match(TokenKind.DEF):
            return self.def_stmt(self.prev())
        if self.match(TokenKind.RETURN):
            return self.return_stmt(self.prev())

        # assignment: IDENT '=' expr ';'
        if self.check(TokenKind.IDENT) and self.toks[self.i + 1].kind == TokenKind.EQ:
            name = self.expect(TokenKind.IDENT, "Expected identifier")
            self.expect(TokenKind.EQ, "Expected '='")
            value = self.expression()
            self.expect(TokenKind.SEMI, "Expected ';' after assignment")
            return A.Assign(name=name, value=value)

        # expression statement
        expr = self.expression()
        self.expect(TokenKind.SEMI, "Expected ';' after expression")
        return A.ExprStmt(expr=expr)

    def block(self) -> A.Block:
        lbrace = self.expect(TokenKind.LBRACE, "Expected '{' to start block")
        stmts: List[A.Stmt] = []
        while not self.check(TokenKind.RBRACE):
            if self.at_end():
                t = self.peek()
                raise ParseError(format_error(self.src, t.line, t.col, "Unterminated block (missing '}')"))
            stmts.append(self.statement())
        self.expect(TokenKind.RBRACE, "Expected '}' after block")
        return A.Block(lbrace=lbrace, statements=stmts)

    def if_stmt(self, if_tok: Token) -> A.If:
        self.expect(TokenKind.LPAREN, "Expected '(' after if")
        cond = self.expression()
        self.expect(TokenKind.RPAREN, "Expected ')' after if condition")
        then_branch = self.block()
        else_branch: Optional[A.Block] = None
        if self.match(TokenKind.ELSE):
            else_branch = self.block()
        return A.If(if_tok=if_tok, cond=cond, then_branch=then_branch, else_branch=else_branch)

    def while_stmt(self, w_tok: Token) -> A.While:
        self.expect(TokenKind.LPAREN, "Expected '(' after while")
        cond = self.expression()
        self.expect(TokenKind.RPAREN, "Expected ')' after while condition")
        body = self.block()
        return A.While(while_tok=w_tok, cond=cond, body=body)

    def def_stmt(self, d_tok: Token) -> A.Def:
        name = self.expect(TokenKind.IDENT, "Expected function name after def")
        self.expect(TokenKind.LPAREN, "Expected '(' after function name")
        params: List[Token] = []
        if not self.check(TokenKind.RPAREN):
            params.append(self.expect(TokenKind.IDENT, "Expected parameter name"))
            while self.match(TokenKind.COMMA):
                params.append(self.expect(TokenKind.IDENT, "Expected parameter name"))
        self.expect(TokenKind.RPAREN, "Expected ')' after parameters")
        body = self.block()
        return A.Def(def_tok=d_tok, name=name, params=params, body=body)

    def return_stmt(self, r_tok: Token) -> A.Return:
        # return; OR return expr;
        if self.match(TokenKind.SEMI):
            return A.Return(return_tok=r_tok, value=None)
        val = self.expression()
        self.expect(TokenKind.SEMI, "Expected ';' after return value")
        return A.Return(return_tok=r_tok, value=val)

    # -------------------------
    # Expressions (Pratt)
    # -------------------------
    PRECEDENCE = {
        TokenKind.OR: 1,
        TokenKind.AND: 2,
        TokenKind.EQEQ: 3,
        TokenKind.NEQ: 3,
        TokenKind.LT: 4,
        TokenKind.LTE: 4,
        TokenKind.GT: 4,
        TokenKind.GTE: 4,
        TokenKind.PLUS: 5,
        TokenKind.MINUS: 5,
        TokenKind.STAR: 6,
        TokenKind.SLASH: 6,
        TokenKind.PERCENT: 6,
    }

    def expression(self) -> A.Expr:
        return self.parse_precedence(0)

    def parse_precedence(self, min_prec: int) -> A.Expr:
        expr = self.prefix()

        while True:
            # Calls: expr '(' args ')'
            if self.check(TokenKind.LPAREN):
                lparen = self.advance()
                args: List[A.Expr] = []
                if not self.check(TokenKind.RPAREN):
                    args.append(self.expression())
                    while self.match(TokenKind.COMMA):
                        args.append(self.expression())
                self.expect(TokenKind.RPAREN, "Expected ')' after arguments")
                expr = A.Call(callee=expr, lparen=lparen, args=args)
                continue

            # Indexing: expr '[' expr ']'
            if self.check(TokenKind.LBRACKET):
                lbr = self.advance()
                idx = self.expression()
                self.expect(TokenKind.RBRACKET, "Expected ']' after index")
                expr = A.Index(target=expr, lbracket=lbr, index=idx)
                continue

            tok = self.peek()
            prec = self.PRECEDENCE.get(tok.kind)
            if prec is None or prec < min_prec:
                break

            op = self.advance()
            right = self.parse_precedence(prec + 1)  # left-associative
            expr = A.Binary(left=expr, op=op, right=right)

        return expr

    def prefix(self) -> A.Expr:
        tok = self.peek()

        if self.match(TokenKind.NUMBER):
            t = self.prev()
            if "." in t.lexeme:
                return A.Number(value=float(t.lexeme), tok=t)
            return A.Number(value=int(t.lexeme), tok=t)

        if self.match(TokenKind.STRING):
            t = self.prev()
            return A.String(value=t.lexeme, tok=t)

        if self.match(TokenKind.TRUE):
            t = self.prev()
            return A.Bool(value=True, tok=t)

        if self.match(TokenKind.FALSE):
            t = self.prev()
            return A.Bool(value=False, tok=t)

        if self.match(TokenKind.NONE):
            t = self.prev()
            return A.NoneLit(tok=t)

        if self.match(TokenKind.IDENT):
            t = self.prev()
            return A.Var(name=t.lexeme, tok=t)

        # list literal: [a, b, c]
        if self.match(TokenKind.LBRACKET):
            lb = self.prev()
            items: List[A.Expr] = []
            if not self.check(TokenKind.RBRACKET):
                items.append(self.expression())
                while self.match(TokenKind.COMMA):
                    items.append(self.expression())
            self.expect(TokenKind.RBRACKET, "Expected ']' after list literal")
            return A.ListLit(lbracket=lb, items=items)

        if self.match(TokenKind.LPAREN):
            expr = self.expression()
            self.expect(TokenKind.RPAREN, "Expected ')' after expression")
            return expr

        if self.match(TokenKind.MINUS, TokenKind.NOT):
            op = self.prev()
            right = self.parse_precedence(7)
            return A.Unary(op=op, right=right)

        raise ParseError(format_error(self.src, tok.line, tok.col, f"Expected expression, got {tok.kind.name}"))
