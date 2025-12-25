from __future__ import annotations
import random
from dataclasses import dataclass
from collections import defaultdict
from typing import List, Dict, Tuple, Optional, Generator

from .exceptions import VarphiTuringMachineHaltedException

@dataclass(init=False)
class VarphiIO:
    tapes: list[str]

    def __init__(self, tapes: list[str], **_ignored):
        self.tapes = tapes


@dataclass(init=False)
class VarphiOutputIO(VarphiIO):
    state: str

    def __init__(self, tapes: list[str], state: str, **_ignored):
        super().__init__(tapes=tapes, **_ignored)
        self.state = state


@dataclass(init=False)
class VarphiDebugIO(VarphiOutputIO):
    heads: list[int]
    line_number: int

    def __init__(
        self,
        tapes: list[str],
        state: str,
        heads: list[int],
        line_number: int,
        **_ignored,
    ):
        super().__init__(tapes=tapes, state=state, **_ignored)
        self.heads = heads
        self.line_number = line_number
    

@dataclass(frozen=True)
class Instruction:
    """Represents an instruction for a Turing machine, detailing the next state,
    symbols to place on each tape, and the directions to move each head.
    """
    next_state: State
    write_symbols: tuple[str, ...]
    shift_directions: tuple[str, ...]
    line_number: int

class State:
    """Represents a state in the Turing machine.

    Supports 'ANY' wildcard in read_symbols.
    - Specific rules take precedence over ANY rules.
    - If multiple ANY rules match, the most specific one (fewest ANYs) wins.
    """
    name: str
    _exact_rules: Dict[Tuple[str, ...], List[Instruction]]
    _wildcard_rules: Dict[Tuple[str, ...], List[Instruction]]

    def __init__(self, name: str) -> None:
        """Initializes a State object."""
        self.name = name
        self._exact_rules = {}
        self._wildcard_rules = {}
    
    def add_instruction(self, read_symbols: tuple[str, ...], instruction: Instruction) -> None:
        """Add a transition rule. Supports 'ANY' as a wildcard in read_symbols."""
        if "ANY" in read_symbols:
            if read_symbols not in self._wildcard_rules:
                self._wildcard_rules[read_symbols] = []
            self._wildcard_rules[read_symbols].append(instruction)
        else:
            if read_symbols not in self._exact_rules:
                self._exact_rules[read_symbols] = []
            self._exact_rules[read_symbols].append(instruction)
    
    def get_instruction(self, read_symbols: tuple[str, ...]) -> Optional[Instruction]:
        """Selects the best instruction for the read symbols."""
        # 1. Optimistic Fast Path: Check for exact match
        if read_symbols in self._exact_rules:
            return random.choice(self._exact_rules[read_symbols])

        # 2. Wildcard Search
        candidates = []
        max_score = -1

        for pattern, instructions in self._wildcard_rules.items():
            if self._matches(pattern, read_symbols):
                score = self._calculate_specificity(pattern)
                
                if score > max_score:
                    max_score = score
                    candidates = instructions.copy()
                elif score == max_score:
                    candidates.extend(instructions)
        
        if not candidates:
            return None
            
        return random.choice(candidates)

    def _matches(self, pattern: tuple[str, ...], concrete: tuple[str, ...]) -> bool:
        if len(pattern) != len(concrete):
            return False
        for p, c in zip(pattern, concrete):
            if p != "ANY" and p != c:
                return False
        return True

    def _calculate_specificity(self, pattern: tuple[str, ...]) -> int:
        return sum(1 for symbol in pattern if symbol != "ANY")


class Tape:
    """A class representing a tape of a Turing machine."""
    _tape: defaultdict[int, str]
    _maximum_accessed_index: int
    _minimum_accessed_index: int

    def __init__(self, initial_values: str) -> None:
        self._tape = defaultdict(lambda: '')  # Tape symbols default to blank
        self._maximum_accessed_index = 0
        self._minimum_accessed_index = 0
        for i, char in enumerate(initial_values):
            self[i] = char
    
    def _update_maximum_and_minimum_indices_accessed(self, index: int) -> None:
        self._maximum_accessed_index = max(self._maximum_accessed_index, index)
        self._minimum_accessed_index = min(self._minimum_accessed_index, index)

    def __getitem__(self, index: int) -> str:
        self._update_maximum_and_minimum_indices_accessed(index)
        return self._tape[index]

    def __setitem__(self, index: int, value: str) -> None:
        self._update_maximum_and_minimum_indices_accessed(index)
        self._tape[index] = value

    def __repr__(self) -> str:
        return "".join(
            self._tape[i] 
            for i in range(self._minimum_accessed_index, self._maximum_accessed_index + 1)
        )
    
    def __str__(self) -> str:
        return self.__repr__()


class Head:
    """A class representing the head of a Turing machine."""
    _tape: Tape
    _current_tape_cell_index: int

    def __init__(self, tape: Tape) -> None:
        self._tape = tape
        self._current_tape_cell_index = 0

    def right(self) -> None:
        self._current_tape_cell_index += 1

    def left(self) -> None:
        self._current_tape_cell_index -= 1

    def read(self) -> str:
        return self._tape[self._current_tape_cell_index]

    def write(self, value: str) -> None:
        self._tape[self._current_tape_cell_index] = value

    def __repr__(self) -> str:
        return str(self._current_tape_cell_index)


class TuringMachine:
    """A class representing a Turing machine.
    
    ASSUMPTION: peek() must be called before every step().
    """
    tapes: tuple[Tape, ...]
    heads: tuple[Head, ...]
    state: State
    unused_tapes: tuple[Tape, ...]
    
    # Simple storage for the instruction decided in peek()
    _next_instruction: Optional[Instruction]

    def __init__(self, k: int, io: VarphiIO, initial_state: State) -> None:
        input_tapes = tuple(Tape(content) for content in io.tapes)
        self.tapes, self.unused_tapes = input_tapes[:k], input_tapes[k:]
        while len(self.tapes) < k:
            self.tapes += (Tape(''),)
        self.heads = tuple(Head(tape) for tape in self.tapes)
        self.state = initial_state
        self._next_instruction = None

    def _get_current_read_symbols(self) -> tuple[str, ...]:
        return tuple(head.read() for head in self.heads)

    def peek(self) -> Optional[Instruction]:
        """Calculates the next instruction and stores it for step()."""
        read_symbols = self._get_current_read_symbols()
        
        # Decide the move now and store it
        self._next_instruction = self.state.get_instruction(read_symbols)
        
        return self._next_instruction

    def step(self) -> None:
        """Executes the instruction stored by the previous peek()."""
        # We assume _next_instruction was just set by peek() and is not None
        instruction = self._next_instruction

        # Execute State Change
        self.state = instruction.next_state
        
        # Execute Tape Operations
        for i, head in enumerate(self.heads):
            # WRITE
            symbol_to_write = instruction.write_symbols[i]
            if symbol_to_write != "ANY":
                head.write(symbol_to_write)
            
            # MOVE
            direction = instruction.shift_directions[i]
            if direction == "LEFT":
                head.left()
            elif direction == "RIGHT":
                head.right()

    def execute(self) -> Generator[VarphiIO]: 
        while True:
            next_instruction = self.peek() # Load the next move
            all_tapes = [str(tape) for tape in self.tapes + self.unused_tapes]
            current_state_name = self.state.name
            if next_instruction is None:
                yield VarphiOutputIO(all_tapes, self.state.name)
                break
            else:
                current_line_number = next_instruction.line_number
                
                heads = [head._current_tape_cell_index for head in self.heads]
                yield VarphiDebugIO(all_tapes, current_state_name, heads, current_line_number)
            self.step() # Execute it