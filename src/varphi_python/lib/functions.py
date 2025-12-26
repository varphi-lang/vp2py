import sys
from .io import VarphiIO, DebugView
from .model import State, TuringMachine

def main(k: int, initial_state: State, debug: bool) -> None:
    io = VarphiIO.from_stdin()
    tm = TuringMachine(k, io.tapes, initial_state)
    time_complexity = 1
    while tm.peek():
        if debug:
            print(DebugView(tm), file=sys.stderr)
        tm.step()
        time_complexity += 1
    print(f"Turing machine has halted at final state '{tm.state.name}'")
    print(f"Time complexity (in steps): {time_complexity}", file=sys.stderr)
    print(f"Space complexity (in cells visited): {sum(head.space_complexity() for head in tm.heads)}", file=sys.stderr)
    print(VarphiIO(tm.tapes))
