from pyraf.lexer import lex
from pyraf.parser import Parser
from pyraf.interpreter import Interpreter

def run_program(src: str) -> None:
    tokens = lex(src)
    program = Parser(tokens, src).parse_program()
    interp = Interpreter(src)
    interp.run(program)

def test_if_else_print(capsys):
    src = """
    x = 12;
    if (x >= 10) { print("ok"); } else { print("no"); }
    """
    run_program(src)
    out = capsys.readouterr().out.strip()
    assert out == "ok"

def test_while_loop_prints_0_1_2(capsys):
    src = """
    i = 0;
    while (i < 3) {
      print(i);
      i = i + 1;
    }
    """
    run_program(src)
    out = capsys.readouterr().out.strip().splitlines()
    assert out == ["0", "1", "2"]

def test_function_return(capsys):
    src = """
    def add(a, b) { return a + b; }
    print(add(2, 5));
    """
    run_program(src)
    out = capsys.readouterr().out.strip()
    assert out == "7"

def test_list_literal_and_index(capsys):
    src = """
    lst = [10, 20, 30];
    print(lst[1]);
    """
    run_program(src)
    out = capsys.readouterr().out.strip()
    assert out == "20"
