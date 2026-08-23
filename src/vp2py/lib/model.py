from __future__ import annotations
from typing import Dict, Tuple, Optional, Set
import random
from collections import defaultdict

from varphi_devkit import (
    BuiltinSymbol,
    Direction,
    Variable,
    Character,
    ReadWriteTupleElement,
    VarphiTransition,
)


class State:
    """A state in the Turing machine."""

    name: str
    transitions: list[VarphiTransition]

    def __init__(self, name: str) -> None:
        """Initialize a new state."""
        self.name = name
        self.transitions = []

    def add_transition(self, transition: VarphiTransition) -> None:
        """Append a VarphiTransition to the state."""
        self.transitions.append(transition)

    def get_transition(
        self, tape_readings: tuple[Character | BuiltinSymbol, ...]
    ) -> Optional[Tuple[VarphiTransition, Dict[Variable, Character | BuiltinSymbol]]]:
        """
        Evaluate current tape readings against the state's transitions to find the highest-specificity match.

        Args:
            tape_readings: A tuple of the actual characters currently read by the machine's heads.

        Returns:
            A tuple containing the winning VarphiTransition and its variable bindings, or None if the machine halts as a result of this situation.
        """
        candidates = []
        best_specificity = None

        for transition in self.transitions:
            bindings = self._check_match(transition.read_symbols, tape_readings)

            if bindings is not None:
                # The transition rule applies
                current_specificity = transition.specificity

                if best_specificity is None:
                    best_specificity = current_specificity

                # Once the best (lowest) specificity is set, we will only consider
                # scores that are the same as that scores
                # Since the transitions have been sorted by the devkit by specificity, we can
                # stop collecting transitions once we see one that has a higher specificity than the
                # best specificity
                elif current_specificity > best_specificity:
                    break

                candidates.append((transition, bindings))

        if not candidates:
            # No transition rules apply, so the machine will halt
            return None

        # Resolve nondeterministic ties
        return random.choice(candidates)

    def _check_match(
        self,
        pattern: tuple[ReadWriteTupleElement, ...],
        readings: tuple[Character | BuiltinSymbol, ...],
    ) -> Optional[Dict[Variable, Character | BuiltinSymbol]]:
        """
        Verify if a given pattern matches the current tape readings and extract variable bindings.

        Returns the variable bindings (or an empty dictionary if there aren't variables) if the pattern applies,
        otherwise returns None
        """
        bindings = {}

        for pattern_symbol, read_symbol in zip(pattern, readings):
            if isinstance(pattern_symbol, Variable):
                if pattern_symbol not in bindings:
                    # Bind the variable to the read symbol
                    bindings[pattern_symbol] = read_symbol
                elif bindings[pattern_symbol] != read_symbol:
                    # We've bound the variable previously, but there's a mismatch
                    # This rule cannot possibly apply
                    return None
            elif pattern_symbol != read_symbol:
                # The pattern and read symbols don't match up, so the rule doesn't apply
                return None
        # If we're here, the rule applies. Return the variable bindings
        return bindings

    def __repr__(self) -> str:
        return f"State({self.name})"


class Tape:
    """Represents a two-way infinite tape of the Turing machine."""

    _tape: defaultdict[int, Character | BuiltinSymbol]
    _min_idx: Optional[int]
    _max_idx: Optional[int]

    def __init__(self, initial_values: list[Character | BuiltinSymbol]) -> None:
        self._tape = defaultdict(lambda: BuiltinSymbol.BLANK)
        self._min_idx = None
        self._max_idx = None

        for i, val in enumerate(initial_values):
            if val != BuiltinSymbol.BLANK:
                self[i] = val

    def __getitem__(self, index: int) -> Character | BuiltinSymbol:
        self._update_bounds(index)
        return self._tape[index]

    def __setitem__(self, index: int, value: Character | BuiltinSymbol) -> None:
        self._update_bounds(index)
        self._tape[index] = value

    def _update_bounds(self, index: int) -> None:
        if self._min_idx is None or self._max_idx is None:
            self._min_idx = index
            self._max_idx = index
        else:
            self._max_idx = max(self._max_idx, index)
            self._min_idx = min(self._min_idx, index)

    def to_string(self, blank_char: str) -> str:
        if self._min_idx is None or self._max_idx is None:
            return ""

        min_i, max_i = self._min_idx, self._max_idx

        while max_i >= min_i and self._tape[max_i] == BuiltinSymbol.BLANK:
            max_i -= 1
        while min_i <= max_i and self._tape[min_i] == BuiltinSymbol.BLANK:
            min_i += 1

        if min_i > max_i:
            return ""

        return "".join(
            blank_char if self._tape[i] == BuiltinSymbol.BLANK else self._tape[i].value
            for i in range(min_i, max_i + 1)
        )

    @property
    def is_empty(self) -> bool:
        return self._min_idx is None


class Head:
    """Represents a read/write head positioned on a specific tape."""

    tape: Tape
    index: int
    user_input_cell_range: Optional[tuple[int, int]]
    new_accessed_cells: Set[int]

    def __init__(self, tape: Tape) -> None:
        self.tape = tape
        self.index = 0
        self.new_accessed_cells = set()

        if tape.is_empty:
            self.user_input_cell_range = None
        else:
            self.user_input_cell_range = (tape._min_idx, tape._max_idx)

    def move(self, direction: Direction) -> None:
        if direction == Direction.LEFT:
            self.index -= 1
        elif direction == Direction.RIGHT:
            self.index += 1

    def read(self) -> Character | BuiltinSymbol:
        self._check_access()
        return self.tape[self.index]

    def write(self, value: Character | BuiltinSymbol) -> None:
        self._check_access()
        self.tape[self.index] = value

    def _check_access(self):
        if self.user_input_cell_range is None:
            self.new_accessed_cells.add(self.index)
        else:
            start, end = self.user_input_cell_range
            if self.index < start or self.index > end:
                self.new_accessed_cells.add(self.index)

    def space_complexity(self) -> int:
        return len(self.new_accessed_cells)


class TuringMachine:
    tapes: tuple[Tape, ...]
    heads: tuple[Head, ...]
    state: State
    state_registry: dict[str, State]
    _next_transition: Optional[VarphiTransition]
    _current_bindings: dict[Variable, Character | BuiltinSymbol]

    def __init__(
        self,
        k: int,
        tapes: tuple[Tape, ...],
        initial_state: State,
        state_registry: dict[str, State],
    ) -> None:
        """
        Initialize the machine.

        Args:
            k: The required number of tapes for this machine configuration.
            tapes: A tuple of initial tapes provided by user input. Missing tapes are generated as blanks.
            initial_state: The entry state of the machine.
            state_registry: A dictionary mapping state names to live State objects.
        """
        self.tapes = tapes  # Keep all tapes so they are printed at the end
        missing_count = k - len(self.tapes)
        if missing_count > 0:
            self.tapes += tuple(Tape([]) for _ in range(missing_count))

        # We only make heads for the first k tapes (we safely ignore excess tapes during execution)
        self.heads = tuple(Head(t) for t in self.tapes[:k])
        self.state = initial_state
        self.state_registry = state_registry
        self._next_transition = None
        self._current_bindings = {}

    def peek(self) -> bool:
        """
        Preview the next transition by evaluating current tape readings against the state.
        This will select and "arm" the machine with the next transition, but won't execute it
        Return True if a next transition has been selected, False if the machine will halt
        """
        reads = tuple(h.read() for h in self.heads)
        result = self.state.get_transition(reads)

        if result is None:
            # No transition applies; halt
            self._next_transition = None
            self._current_bindings = {}
            return False

        self._next_transition, self._current_bindings = result
        return True

    def step(self) -> None:
        """Execute the transition locked in by the previous call to peek()."""
        transition = self._next_transition
        bindings = self._current_bindings

        if transition is None:
            return

        # Perform the string-to-object dictionary lookup here
        self.state = self.state_registry[transition.next_state]

        for i, head in enumerate(self.heads):
            sym = transition.write_symbols[i]
            val_to_write = bindings[sym] if isinstance(sym, Variable) else sym
            head.write(val_to_write)
            head.move(transition.shift_directions[i])
