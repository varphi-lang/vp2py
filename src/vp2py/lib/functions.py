import sys
from .io import VarphiIO, DebugView
from .model import State, Tape, TuringMachine

def run_machine(
    k: int,
    initial_state: State,
    state_registry: dict,
    tapes: tuple[Tape, ...],
    debug: bool = False,
    blank_char: str = "_",
) -> TuringMachine:
    """Programmatic API to execute a Turing machine and return its final state."""
    tm = TuringMachine(k, tapes, initial_state, state_registry)
    time_complexity = 0
    SEPARATOR = "-" * 60

    while tm.peek():
        if debug:
            print(f"\n{SEPARATOR}", file=sys.stderr)
            print(f"STEP {time_complexity + 1} [State: {tm.state.name}]", file=sys.stderr)
            print(f"{SEPARATOR}", file=sys.stderr)
            print(DebugView(tm, blank_char), file=sys.stderr)
            try:
                input("\n>> Press ENTER to step forward...")
            except (KeyboardInterrupt, EOFError):
                print("\nInterrupted.", file=sys.stderr)
                return tm

        tm.step()
        time_complexity += 1

    if debug and sys.stdout.isatty():
        print(f"\n{SEPARATOR}", file=sys.stderr)
        print(f"HALTED at state '{tm.state.name}'", file=sys.stderr)
        print(f"Time taken: {time_complexity} steps", file=sys.stderr)
        print(
            f"Space used: {sum(head.space_complexity() for head in tm.heads)} cells",
            file=sys.stderr,
        )

    return tm

def main(
    k: int,
    initial_state: State,
    state_registry: dict,
    debug: bool,
    blank_char: str = "_",
) -> None:
    """CLI entry point handling stdin/stdout."""
    io = VarphiIO.from_stdin(blank_char)
    tm = run_machine(k, initial_state, state_registry, io.tapes, debug, blank_char)
    VarphiIO(tm.tapes).print(blank_char, tm.state.name)