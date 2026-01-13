import argparse
from pathlib import Path

from pyraf.lexer import lex
from pyraf.errors import PyRafError


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
        from pyraf.parser import Parser as RafParser
        from pyraf.interpreter import Interpreter

        path = Path(args.file)
        if not path.exists():
            raise SystemExit(f"File not found: {path}")

        src = path.read_text(encoding="utf-8")

        try:
            tokens = lex(src)
            program = RafParser(tokens, src).parse_program()
            interp = Interpreter(src)
            interp.run(program)
        except PyRafError as e:
            print(e)
            raise SystemExit(1)

        return

    if args.cmd == "repl":
        from pyraf.parser import Parser as RafParser
        from pyraf.interpreter import Interpreter
        from pyraf.runtime import Env

        print("PyRaf REPL. End statements with ';'. Use { } for blocks. Type 'quit' to exit.")

        interp = Interpreter(src="")
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

            stripped = buffer.strip()
            if not stripped:
                buffer = ""
                continue
            if not (stripped.endswith(";") or stripped.endswith("}")):
                continue

            try:
                tokens = lex(buffer)
                program = RafParser(tokens, buffer).parse_program()
                interp.src = buffer
                interp.run_in_env(program, env)
            except PyRafError as e:
                print(e)
            finally:
                buffer = ""
        return


if __name__ == "__main__":
    main()
