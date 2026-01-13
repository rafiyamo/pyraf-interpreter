from pathlib import Path

from pyraf.lexer import lex
from pyraf.parser import Parser
from pyraf.interpreter import Interpreter
from pyraf.runtime import Env


def test_import_runs_once_and_defines_symbols(tmp_path, capsys):
    # tmp project layout:
    # tmp/
    #   lib/
    #     math.raf
    #   main.raf
    lib = tmp_path / "lib"
    lib.mkdir()

    (lib / "math.raf").write_text('def square(x) { return x * x; }\n', encoding="utf-8")

    main_src = 'import "lib/math.raf";\nprint(square(9));\n'
    main_file = tmp_path / "main.raf"
    main_file.write_text(main_src, encoding="utf-8")

    tokens = lex(main_src)
    program = Parser(tokens, main_src).parse_program()

    interp = Interpreter(main_src, base_dir=str(tmp_path))
    env = Env(interp.globals)
    interp.run_in_env(program, env)

    out = capsys.readouterr().out.strip()
    assert out == "81"

    # importing again should do nothing extra (cached)
    interp.run_in_env(program, env)
    out2 = capsys.readouterr().out.strip()
    assert out2 == "81"