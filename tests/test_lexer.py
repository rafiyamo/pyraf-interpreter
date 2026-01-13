from pyraf.lexer import lex
from pyraf.tokens import TokenKind

def test_lex_basic_tokens():
    src = 'x = 12; if (x >= 10) { print("ok"); }'
    toks = lex(src)
    kinds = [t.kind for t in toks]
    assert kinds[:8] == [
        TokenKind.IDENT, TokenKind.EQ, TokenKind.NUMBER, TokenKind.SEMI,
        TokenKind.IF, TokenKind.LPAREN, TokenKind.IDENT, TokenKind.GTE
    ]
    assert kinds[-1] == TokenKind.EOF
