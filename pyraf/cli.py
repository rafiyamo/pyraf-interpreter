import argparse
from pathlib import Path

from pyraf.lexer import lex
from pyraf.parser import Parser
from pyraf.errors import PyRafError
from pyraf.interpreter import Interpreter


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pyraf",
        description="PyRaf — a Python-inspired interpreter (work in progress)."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Run a .raf file")
    run_p.add_argument("file", type=str)

    sub.add_parser("repl", help="Start the PyRaf REPL")

    args = parser.parse_args()

    if args.cmd == "run":
        path = Path(args.file)
        if not path.exists():
            raise SystemExit(f"File not found: {path}")

        src = path.read_text(encoding="utf-8")

        try:
            tokens = lex(src)
            program = Parser(tokens, src).parse_program()
        except PyRafError as e:
            print(e)
            raise SystemExit(1)

        
        interp = Interpreter(src)
        interp.run(program)
        return

    if args.cmd == "repl":
        print("PyRaf REPL. End statements with ';'. Use { } for blocks. Type 'quit' to exit.")
        # persistent session env
        from pyraf.interpreter import Interpreter
        from pyraf.runtime import Env
        from pyraf.parser import Parser

        interp = Interpreter(src="")  # src will be set per run
        env = Env(interp.globals)

        buffer = ""
        while True:
            try:
                prompt = ">>> " if buffer == "" else "... "
                line = input(prompt)
            except EOFError:
                print()
                break

            if buffer == "" and line.strip() in {"quit", "exit"}:
                break

            buffer += line + "\n"

            # Only try to run when it looks like the user finished a statement/block.
            # Heuristic: last non-whitespace ends with ';' or '}'.
            stripped = buffer.strip()
            if not stripped:
                buffer = ""
                continue
            if not (stripped.endswith(";") or stripped.endswith("}")):
                continue

            try:
                tokens = lex(buffer)
                program = Parser(tokens, buffer).parse_program()
                interp.src = buffer
                interp.run_in_env(program, env)
            except PyRafError as e:
                print(e)
            finally:
                buffer = ""
        return



if __name__ == "__main__":
    main()
