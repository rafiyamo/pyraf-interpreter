from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto

class TokenKind(Enum):
    # Single-character
    LPAREN = auto(); RPAREN = auto()
    LBRACE = auto(); RBRACE = auto()
    LBRACKET = auto(); RBRACKET = auto()
    COMMA = auto(); SEMI = auto()

    PLUS = auto(); MINUS = auto()
    STAR = auto(); SLASH = auto(); PERCENT = auto()

    # One/two character operators
    EQ = auto()
    EQEQ = auto()
    NEQ = auto()
    LT = auto(); LTE = auto()
    GT = auto(); GTE = auto()

    # Literals / identifiers
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()

    # Keywords
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    DEF = auto()
    RETURN = auto()

    TRUE = auto()
    FALSE = auto()
    NONE = auto()

    AND = auto()
    OR = auto()
    NOT = auto()

    EOF = auto()

@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    line: int
    col: int
