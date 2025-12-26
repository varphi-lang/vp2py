from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Iterable
import random
from varphi_devkit import WILDCARD, BLANK, LEFT, RIGHT
from collections import defaultdict


@dataclass(frozen=True)
class Instruction:
    next_state: State
    write_symbols: tuple[str, ...]
    shift_directions: tuple[str, ...]
    line_number: int

class State:
    name: str
    _exact_rules: Dict[Tuple[str, ...], List[Instruction]]
    _wildcard_rules: Dict[Tuple[str, ...], List[Instruction]]

    def __init__(self, name: str) -> None:
        self.name = name
        self._exact_rules = {}
        self._wildcard_rules = {}
    
    def add_instruction(self, read_symbols: tuple[str, ...], instruction: Instruction) -> None:
        if WILDCARD in read_symbols:
            if read_symbols not in self._wildcard_rules:
                self._wildcard_rules[read_symbols] = []
            self._wildcard_rules[read_symbols].append(instruction)
        else:
            if read_symbols not in self._exact_rules:
                self._exact_rules[read_symbols] = []
            self._exact_rules[read_symbols].append(instruction)
    
    def get_instruction(self, read_symbols: tuple[str, ...]) -> Optional[Instruction]:
        if read_symbols in self._exact_rules:
            return random.choice(self._exact_rules[read_symbols])

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
        
        if not candidates: return None
        return random.choice(candidates)

    def _matches(self, pattern: tuple[str, ...], concrete: tuple[str, ...]) -> bool:
        return all(p == WILDCARD or p == c for p, c in zip(pattern, concrete))

    def _calculate_specificity(self, pattern: tuple[str, ...]) -> int:
        return sum(1 for symbol in pattern if symbol != WILDCARD)

    def __repr__(self) -> str:
        return f"State({self.name})"

class Tape:
    _tape: defaultdict[int, str]
    _min_idx: int
    _max_idx: int

    def __init__(self, initial_values: Iterable[str]) -> None:
        self._tape = defaultdict(lambda: BLANK) 
        self._min_idx = 0
        self._max_idx = 0
        for i, char in enumerate(initial_values):
            self[i] = char
    
    def __getitem__(self, index: int) -> str:
        self._update_bounds(index)
        return self._tape[index]

    def __setitem__(self, index: int, value: str) -> None:
        self._update_bounds(index)
        self._tape[index] = value

    def _update_bounds(self, index: int) -> None:
        self._max_idx = max(self._max_idx, index)
        self._min_idx = min(self._min_idx, index)

    def to_string(self) -> str:
        return "".join(self._tape[i] for i in range(self._min_idx, self._max_idx + 1))

class Head:
    tape: Tape
    index: int
    user_input_cell_range: tuple[int, int]
    new_accessed_cells: set[int]

    def __init__(self, tape: Tape) -> None:
        self.tape = tape
        self.index = 0
        self.user_input_cell_range = (tape._min_idx, tape._max_idx)
        self.new_accessed_cells = set()

    def move(self, direction: str) -> None:
        if direction == LEFT:
            self.index -= 1
        elif direction == RIGHT:
            self.index += 1

    def read(self) -> str:
        if self.user_input_cell_range == (0, 0) or self.index < self.user_input_cell_range[0] or self.index > self.user_input_cell_range[1]:
            self.new_accessed_cells.add(self.index)
        return self.tape[self.index]

    def write(self, value: str) -> None:
        if self.user_input_cell_range == (0, 0) or self.index < self.user_input_cell_range[0] or self.index > self.user_input_cell_range[1]:
            self.new_accessed_cells.add(self.index)
        self.tape[self.index] = value
    
    def space_complexity(self) -> int:
        return len(self.new_accessed_cells)

class TuringMachine:
    def __init__(self, k: int, tapes: tuple[Tape, ...], initial_state: State) -> None:
        self.tapes = tapes
        while len(self.tapes) < k:
            self.tapes += (Tape([]),)
        
        self.heads = tuple(Head(t) for t in self.tapes[:k])
        self.state = initial_state
        self._next_instruction: Optional[Instruction] = None

    def peek(self) -> bool:
        """
        Looks up the next instruction based on current tape symbols.
        Stores it in self._next_instruction.
        Returns False if the machine halts (no transition found).
        """
        reads = tuple(h.read() for h in self.heads)
        self._next_instruction = self.state.get_instruction(reads)
        return self._next_instruction is not None

    def step(self) -> None:
        """
        Executes the instruction stored in self._next_instruction.
        Assumes peek() has been called previously.
        """
        instr = self._next_instruction
        
        # Guard clause in case peek() failed or wasn't called
        if instr is None:
            return

        # 1. Update State
        self.state = instr.next_state

        # 2. Write and Move Heads
        for i, head in enumerate(self.heads):
            sym = instr.write_symbols[i]
            if sym != WILDCARD:
                head.write(sym)
            head.move(instr.shift_directions[i])