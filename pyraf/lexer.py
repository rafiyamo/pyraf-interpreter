from __future__ import annotations
from typing import List
from .tokens import Token, TokenKind
from .errors import LexError, format_error

KEYWORDS = {
    "if": TokenKind.IF,
    "else": TokenKind.ELSE,
    "while": TokenKind.WHILE,
    "def": TokenKind.DEF,
    "return": TokenKind.RETURN,
    "true": TokenKind.TRUE,
    "false": TokenKind.FALSE,
    "none": TokenKind.NONE,
    "and": TokenKind.AND,
    "or": TokenKind.OR,
    "not": TokenKind.NOT,
    "import": TokenKind.IMPORT,
}

SINGLE = {
    "(": TokenKind.LPAREN, ")": TokenKind.RPAREN,
    "{": TokenKind.LBRACE, "}": TokenKind.RBRACE,
    "[": TokenKind.LBRACKET, "]": TokenKind.RBRACKET,
    ",": TokenKind.COMMA, ";": TokenKind.SEMI,
    "+": TokenKind.PLUS, "-": TokenKind.MINUS,
    "*": TokenKind.STAR, "/": TokenKind.SLASH, "%": TokenKind.PERCENT,
}

def lex(src: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    line = 1
    col = 1

    def add(kind: TokenKind, lexeme: str, l: int, c: int) -> None:
        tokens.append(Token(kind, lexeme, l, c))

    while i < len(src):
        ch = src[i]

        # whitespace
        if ch in " \t\r":
            i += 1
            col += 1
            continue
        if ch == "\n":
            i += 1
            line += 1
            col = 1
            continue

        # comment: //
        if ch == "/" and i + 1 < len(src) and src[i + 1] == "/":
            while i < len(src) and src[i] != "\n":
                i += 1
                col += 1
            continue

        # string: "..."
        if ch == '"':
            start_line, start_col = line, col
            i += 1
            col += 1
            value = ""
            while i < len(src) and src[i] != '"':
                if src[i] == "\\" and i + 1 < len(src):
                    esc = src[i + 1]
                    mapping = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                    value += mapping.get(esc, esc)
                    i += 2
                    col += 2
                else:
                    if src[i] == "\n":
                        value += "\n"
                        i += 1
                        line += 1
                        col = 1
                    else:
                        value += src[i]
                        i += 1
                        col += 1
            if i >= len(src):
                raise LexError(format_error(src, start_line, start_col, "Unterminated string literal"))
            i += 1
            col += 1
            add(TokenKind.STRING, value, start_line, start_col)
            continue

        # number: int or float
        if ch.isdigit():
            start_line, start_col = line, col
            j = i
            has_dot = False
            while j < len(src) and (src[j].isdigit() or (src[j] == "." and not has_dot)):
                if src[j] == ".":
                    has_dot = True
                j += 1
            lexeme = src[i:j]
            add(TokenKind.NUMBER, lexeme, start_line, start_col)
            col += (j - i)
            i = j
            continue

        # ident/keyword
        if ch.isalpha() or ch == "_":
            start_line, start_col = line, col
            j = i
            while j < len(src) and (src[j].isalnum() or src[j] == "_"):
                j += 1
            text = src[i:j]
            kind = KEYWORDS.get(text, TokenKind.IDENT)
            add(kind, text, start_line, start_col)
            col += (j - i)
            i = j
            continue

        # two-char operators
        if i + 1 < len(src):
            pair = src[i:i+2]
            if pair == "==":
                add(TokenKind.EQEQ, pair, line, col); i += 2; col += 2; continue
            if pair == "!=":
                add(TokenKind.NEQ, pair, line, col); i += 2; col += 2; continue
            if pair == "<=":
                add(TokenKind.LTE, pair, line, col); i += 2; col += 2; continue
            if pair == ">=":
                add(TokenKind.GTE, pair, line, col); i += 2; col += 2; continue

        # one-char operators
        if ch == "=":
            add(TokenKind.EQ, ch, line, col); i += 1; col += 1; continue
        if ch == "<":
            add(TokenKind.LT, ch, line, col); i += 1; col += 1; continue
        if ch == ">":
            add(TokenKind.GT, ch, line, col); i += 1; col += 1; continue

        # punctuation/operators
        if ch in SINGLE:
            add(SINGLE[ch], ch, line, col)
            i += 1
            col += 1
            continue

        raise LexError(format_error(src, line, col, f"Unexpected character: {ch!r}"))

    tokens.append(Token(TokenKind.EOF, "", line, col))
    return tokens
