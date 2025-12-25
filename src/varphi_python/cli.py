from pathlib import Path
import typer


def varphi_python(
    input_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="Path to input Varphi source file"
    ),
    debug: bool = typer.Option(
        False,
        "--debug/--no-debug",
        help="Compile with debugging capabilities",
    ),
):
    """Compile a Varphi source code file to Python"""
    from .core import VarphiToPythonCompiler
    compiler = VarphiToPythonCompiler()
    if debug:
        compiler.toggle_compilation_with_debugging()
    typer.echo(compiler.compile(
        input_file.read_text(encoding="utf-8"),  
    ).encode())

def main():
    typer.run(varphi_python)

if __name__ == "__main__":
    main()
