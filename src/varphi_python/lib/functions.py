import sys
import json
from .types import State, TuringMachine, VarphiIO
from dataclasses import asdict

def send(msg: str):
    data = msg.encode("utf-8")
    sys.stdout.write(f"{len(data)}\n")
    sys.stdout.flush()
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()

def _readline_bytes() -> bytes:
    line = sys.stdin.buffer.readline()
    if not line:
        raise EOFError("Missing length")
    return line

def _read_exact(n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = sys.stdin.buffer.read(n - len(data))
        if not chunk:
            break
        data += chunk
    if len(data) != n:
        raise EOFError("Incomplete message")
    return data

def recv() -> str:
    line = _readline_bytes()
    try:
        n = int(line.strip())
    except ValueError:
        raise ValueError(f"Invalid length line: {line!r}")

    body = _read_exact(n)
    return body.decode("utf-8")



def main(k: int, initial_state: State, debug: bool) -> None:
    raw_input = recv()
    io = VarphiIO(**json.loads(raw_input))
    tm = TuringMachine(k, io, initial_state)
    output = None
    for output in tm.execute():
        if debug:
            print(asdict(output), file=sys.stderr)
            input("Press Enter to continue...")
    send(str(asdict(output)))
