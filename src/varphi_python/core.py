from varphi_devkit import VarphiCompiler, VarphiTransition, VarphiSyntaxError

class VarphiToPythonCompiler(VarphiCompiler):
    _initial_state: str | None
    _seen_state_names: set[str]
    _output: str
    _number_of_tapes: int | None
    compilation_with_debugging: bool

    def __init__(self):
        self._initial_state = None
        self._seen_state_names = set()
        self._number_of_tapes = None
        self._output = """from varphi_python.lib import Instruction, State, main
if __name__ == "__main__":
"""
        self.compilation_with_debugging = False
        super().__init__()
    
    def handle_transition(self, transition: VarphiTransition):
        if self._number_of_tapes is None:
            self._number_of_tapes = len(transition.read_symbols)
        else:
            if len(transition.read_symbols) != self._number_of_tapes:
                raise VarphiSyntaxError(f"Tuple lengths across transitions must be equal. Expected {self._number_of_tapes} but got {len(transition.read_symbols)}.", transition.line_number, 0)
        if transition.current_state not in self._seen_state_names:
            self._output += f"    {transition.current_state} = State(\"{transition.current_state}\")\n"
            if self._initial_state is None:
                self._initial_state = transition.current_state
            self._seen_state_names.add(transition.current_state)
        if transition.next_state not in self._seen_state_names:
            self._output += f"    {transition.next_state} = State(\"{transition.next_state}\")\n"
            self._seen_state_names.add(transition.next_state)
        instruction = (
            f"Instruction(next_state={transition.next_state}, "
            f"write_symbols={transition.write_symbols}, "
            f"shift_directions={transition.shift_directions}, "
            f"line_number={transition.line_number})"
        )
        self._output += (
            f"    {transition.current_state}.add_instruction("
            f"read_symbols={transition.read_symbols}, instruction={instruction})\n"
        )
    
    def generate_compiled_program(self) -> str:
        self._output += f"    main({self._number_of_tapes}, {self._initial_state}, {self.compilation_with_debugging})\n"
        return self._output

    def toggle_compilation_with_debugging(self) -> None:
        self.compilation_with_debugging = not self.compilation_with_debugging
