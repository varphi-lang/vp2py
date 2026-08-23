import sys
from pathlib import Path
from typing import Optional
import typer


def vp2py(
    input_file: Optional[Path] = typer.Argument(
        None,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Path to input Varphi source file. If omitted, reads from standard input.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug/--no-debug",
        help="Compile with debugging capabilities",
    ),
):
    """Compile a Varphi source code file to Python"""
    from .compiler import VarphiToPythonCompiler

    compiler = VarphiToPythonCompiler()
    if debug:
        compiler.toggle_debug()

    if input_file:
        source_code = input_file.read_text(encoding="utf-8")
    else:
        # Fallback to stdin if no file is provided
        source_code = sys.stdin.read()

    # Compile, and print result to stdout
    result = compiler.compile(source_code)
    typer.echo(result)


def main():
    typer.run(vp2py)


if __name__ == "__main__":
    main()