from pyraf.lexer import lex
from pyraf.parser import Parser
from pyraf.compiler import compile_program
from pyraf.vm import VM


def run_vm(src: str) -> None:
    tokens = lex(src)
    program = Parser(tokens, src).parse_program()
    chunk = compile_program(program, src, name="<test>")
    VM(src).run(chunk)


def test_vm_if_else_print(capsys):
    src = """
    x = 12;
    if (x >= 10) { print("ok"); } else { print("no"); }
    """
    run_vm(src)
    out = capsys.readouterr().out.strip()
    assert out == "ok"


def test_vm_function_return(capsys):
    src = """
    def add(a, b) { return a + b; }
    print(add(2, 5));
    """
    run_vm(src)
    out = capsys.readouterr().out.strip()
    assert out == "7"
