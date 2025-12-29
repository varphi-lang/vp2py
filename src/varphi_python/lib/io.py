from __future__ import annotations
import sys
from dataclasses import dataclass
from typing import Tuple
from .model import Tape, TuringMachine
from .exceptions import VarphiRuntimeError
from varphi_devkit import BLANK


@dataclass(frozen=True)
class VarphiIO:
    tapes: Tuple[Tape, ...]

    @staticmethod
    def from_stdin() -> VarphiIO:
        if sys.stdin.isatty():
            print("Number of input tapes: ", end="", file=sys.stderr, flush=True)
        header = sys.stdin.readline()
        if not header:
            return VarphiIO(tuple())

        try:
            num_tapes = int(header.strip())
        except ValueError:
            raise VarphiRuntimeError(f"Runtime Error: Expected an integer for number of tapes, got \"{header.strip()}\".")
        if num_tapes <= 0:
            raise VarphiRuntimeError(f"Runtime Error: Expected a positive number of tapes, got \"{num_tapes}\".")
        tapes = []
        for i in range(num_tapes):
            if sys.stdin.isatty():
                print(f"Tape {i + 1}: ", end="", file=sys.stderr, flush=True)
            line = sys.stdin.readline().strip()
            tapes.append(Tape(line))
        return VarphiIO(tuple(tapes))

    def print(self) -> None:
        # Check if we are printing to a human (TTY) or a pipe
        show_labels = sys.stdout.isatty()

        if show_labels:
            print("Number of tapes: ", end="", file=sys.stderr, flush=True)

        print(len(self.tapes))

        for i, tape in enumerate(self.tapes):
            if show_labels:
                print(f"Tape {i + 1}: ", end="", file=sys.stderr, flush=True)
            print(tape.to_string())


@dataclass
class DebugView:
    machine: TuringMachine

    def __str__(self) -> str:
        line_number = self.machine._next_instruction.line_number
        lines = [f"State: {self.machine.state.name} (Line {line_number})"]

        # Calculate the global maximum "interesting" radius across ALL tapes
        max_radius = 0
        for head in self.machine.heads:
            # If tape is empty, radius is 0
            if not head.tape._tape:
                continue
                
            # Calculate distance from head to the furthest written character (left or right)
            dist_left = abs(head.index - head.tape._min_idx)
            dist_right = abs(head.index - head.tape._max_idx)
            
            # Keep the largest distance found so far
            max_radius = max(max_radius, dist_left, dist_right)

        # Render all tapes using this fixed radius
        for i, head in enumerate(self.machine.heads):
            start = head.index - max_radius
            end = head.index + max_radius
            
            chars = []
            for idx in range(start, end + 1):
                val = head.tape._tape.get(idx, BLANK)
                if idx == head.index:
                    chars.append(f"[{val}]")
                else:
                    chars.append(val)
            
            # Note: The prefix "Tape i: " must be consistent length for perfect alignment.
            # If you have > 10 tapes, you might want to use f"Tape {i:<2}: "
            lines.append(f"Tape {i}: {''.join(chars)}")

        return "\n".join(lines)