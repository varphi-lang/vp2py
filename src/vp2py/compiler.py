from varphi_devkit import (
    VarphiCompiler,
    BuiltinSymbol,
    Variable,
    Direction,
    Character,
    ReadWriteTupleElement,
)

TEMPLATE = """\
from vp2py.lib import State, main
from varphi_devkit import BuiltinSymbol, Direction, Variable, Character, VarphiTransition

# --- State Registry ---
state_registry = {{
{state_registry_entries}
}}

# --- Transition Definitions ---
{instruction_definitions}

# --- Runtime Setup ---
initial_state = state_registry['{initial_state}']
k = {num_tapes}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Varphi Turing Machine Runtime")
    parser.add_argument("--debug", action="store_true", default={debug_mode}, help="Enable step-by-step debug mode")
    parser.add_argument("-b", "--blank-char", type=str, default="_", help="Character representing a BLANK cell in input/output (Default: _)")
    args = parser.parse_args()
    
    # Pass the state_registry to main!
    main(k, initial_state, state_registry, args.debug, args.blank_char)
"""


class VarphiToPythonCompiler(VarphiCompiler):
    debug_mode: bool

    def __init__(self):
        super().__init__()
        self.debug_mode = False

    def toggle_debug(self):
        self.debug_mode = not self.debug_mode

    def _format_symbol(self, s: ReadWriteTupleElement) -> str:
        """Converts devkit symbol objects to valid strings to inject into the compiled code."""
        if s == BuiltinSymbol.BLANK:
            return "BuiltinSymbol.BLANK"
        if isinstance(s, Variable):
            return f"Variable({s.id})"
        if isinstance(s, Character):
            return f"Character({repr(s.value)})"
        raise ValueError(f"Unknown symbol type: {type(s)}")

    def _format_direction(self, d: Direction) -> str:
        """Converts devkit direction enums to valid Python code strings."""
        return f"Direction.{d.name}"

    def _generate_compiled_program(self) -> str:
        # Use the devkit's pre-discovered states directly
        all_states = self.states

        # Build the dictionary mapping strings to the State objects directly to avoid keyword collisions
        registry_entries = "\n".join(
            f"    '{name}': State('{name}')," for name in all_states
        )

        # Map the pre-sorted IR transitions to VarphiTransition instantiations
        instructions_code = []
        for transitions in self.ir.values():
            for t in transitions:
                read_str = "(" + ", ".join(
                    self._format_symbol(s) for s in t.read_symbols
                )
                read_str += ",)" if len(t.read_symbols) == 1 else ")"

                write_str = "(" + ", ".join(
                    self._format_symbol(s) for s in t.write_symbols
                )
                write_str += ",)" if len(t.write_symbols) == 1 else ")"

                shift_str = "(" + ", ".join(
                    self._format_direction(d) for d in t.shift_directions
                )
                shift_str += ",)" if len(t.shift_directions) == 1 else ")"

                code = (
                    f"state_registry['{t.current_state}'].add_transition(\n"
                    f"    VarphiTransition(\n"
                    f"        current_state='{t.current_state}',\n"
                    f"        read_symbols={read_str},\n"
                    f"        next_state='{t.next_state}',\n"
                    f"        write_symbols={write_str},\n"
                    f"        shift_directions={shift_str},\n"
                    f"        line_number={t.line_number}\n"
                    f"    )\n"
                    f")"
                )
                instructions_code.append(code)

        return TEMPLATE.format(
            state_registry_entries=registry_entries,
            instruction_definitions="\n\n".join(instructions_code),
            initial_state=self.initial_state,
            num_tapes=self._tape_count,
            debug_mode=self.debug_mode,
        )
