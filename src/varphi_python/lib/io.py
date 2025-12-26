from __future__ import annotations
import sys
from dataclasses import dataclass
from typing import Tuple
from .model import Tape, TuringMachine

@dataclass(frozen=True)
class VarphiIO:
    tapes: Tuple[Tape, ...]

    @staticmethod
    def from_stdin() -> VarphiIO:
        try:
            header = sys.stdin.readline()
            if not header: return VarphiIO(tuple())
            
            num_tapes = int(header.strip())
            tapes = []
            for _ in range(num_tapes):
                line = sys.stdin.readline().strip()
                tapes.append(Tape(list(line)))
            return VarphiIO(tuple(tapes))
        except ValueError:
            return VarphiIO(tuple())

    def __str__(self) -> str:
        lines = [str(len(self.tapes))]
        for tape in self.tapes:
            lines.append(tape.to_string())
        return "\n".join(lines)

@dataclass
class DebugView:
    machine: TuringMachine

    def __str__(self) -> str:
        line_number = self.machine._next_instruction.line_number
        lines = [f"State: {self.machine.state.name} (Line {line_number})"]
        
        for i, tape in enumerate(self.machine.tapes):
            if i < len(self.machine.heads):
                head = self.machine.heads[i]
                start = min(tape._min_idx, head.index)
                end = max(tape._max_idx, head.index)
                
                chars = []
                markers = []
                
                for idx in range(start, end + 1):
                    val = tape._tape[idx]
                    chars.append(val)
                    
                    width = max(1, len(val))
                    if idx == head.index:
                        markers.append("^".center(width))
                    else:
                        markers.append(" " * width)
                
                prefix = f"Tape {i}: "
                lines.append(f"{prefix}{''.join(chars)}")
                lines.append(" " * len(prefix) + "".join(markers))
            else:
                lines.append(f"Tape {i}: {tape.to_string()}")
        
        return "\n".join(lines)