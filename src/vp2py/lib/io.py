from __future__ import annotations
import sys
from dataclasses import dataclass
from typing import Tuple, Optional
from .model import Tape, TuringMachine
from .exceptions import VarphiRuntimeError
from varphi_devkit import BuiltinSymbol, Character


@dataclass(frozen=True)
class VarphiIO:
    tapes: Tuple[Tape, ...]

    @staticmethod
    def from_stdin(blank_char: str) -> VarphiIO:
        if sys.stdin.isatty():
            print("Number of input tapes: ", end="", file=sys.stderr, flush=True)

        header = sys.stdin.readline()
        if not header:
            return VarphiIO(tuple())

        try:
            num_tapes = int(header.strip())
        except ValueError:
            raise VarphiRuntimeError(
                f'Runtime Error: Expected an integer for number of tapes, got "{header.strip()}".'
            )
        if num_tapes <= 0:
            raise VarphiRuntimeError(
                f'Runtime Error: Expected a positive number of tapes, got "{num_tapes}".'
            )

        tapes = []
        for i in range(num_tapes):
            if sys.stdin.isatty():
                print(f"Tape {i + 1}: ", end="", file=sys.stderr, flush=True)

            line = sys.stdin.readline().strip("\r\n")

            parsed_tape = []
            for char in line:
                if char == blank_char:
                    parsed_tape.append(BuiltinSymbol.BLANK)
                else:
                    parsed_tape.append(Character(char))

            tapes.append(Tape(parsed_tape))

        return VarphiIO(tuple(tapes))

    def print(self, blank_char: str, final_state: Optional[str] = None) -> None:
        show_labels = sys.stdout.isatty()
        if show_labels:
            print("Number of tapes: ", end="", file=sys.stderr, flush=True)

        print(len(self.tapes))

        for i, tape in enumerate(self.tapes):
            if show_labels:
                print(f"Tape {i + 1}: ", end="", file=sys.stderr, flush=True)
            print(tape.to_string(blank_char))

        if final_state is not None:
            if show_labels:
                print("Final State: ", end="", file=sys.stderr, flush=True)
            print(final_state)


@dataclass
class DebugView:
    machine: TuringMachine
    blank_char: str

    def __str__(self) -> str:
        line_number = (
            self.machine._next_transition.line_number
            if self.machine._next_transition
            else "?"
        )
        lines = [f"State: {self.machine.state.name} (Line {line_number})"]

        max_radius = 0
        for head in self.machine.heads:
            if not head.tape._tape:
                continue

            dist_left = (
                abs(head.index - head.tape._min_idx)
                if head.tape._min_idx is not None
                else 0
            )
            dist_right = (
                abs(head.index - head.tape._max_idx)
                if head.tape._max_idx is not None
                else 0
            )
            max_radius = max(max_radius, dist_left, dist_right)

        for i, head in enumerate(self.machine.heads):
            start = head.index - max_radius
            end = head.index + max_radius

            chars = []
            for idx in range(start, end + 1):
                val = head.tape._tape.get(idx, BuiltinSymbol.BLANK)
                val_str = self.blank_char if val == BuiltinSymbol.BLANK else val.value

                if idx == head.index:
                    chars.append(f"[{val_str}]")
                else:
                    chars.append(val_str)

            lines.append(f"Tape {i + 1}: {''.join(chars)}")

        return "\n".join(lines)