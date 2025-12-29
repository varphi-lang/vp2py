from varphi_python.lib.model import State, Instruction


def make_instr(next_state_name="end") -> Instruction:
    return Instruction(
        next_state=State(next_state_name),
        write_symbols=("w",),
        shift_directions=("STAY",),
        line_number=1,
    )


class TestPatternMatching:
    def test_literal_match(self):
        s = State("test")
        s.add_instruction(("A", "B"), make_instr())

        instr, bindings = s.get_instruction(("A", "B"))
        assert instr is not None
        assert bindings == {}

        assert s.get_instruction(("A", "C")) is None

    def test_variable_binding_success(self):
        s = State("test")
        s.add_instruction(("$x", "B"), make_instr())

        instr, bindings = s.get_instruction(("Z", "B"))
        assert instr is not None
        assert bindings == {"$x": "Z"}

    def test_variable_consistency_constraint(self):
        s = State("test")
        s.add_instruction(("$x", "$x"), make_instr())

        instr, bindings = s.get_instruction(("9", "9"))
        assert instr is not None
        assert bindings == {"$x": "9"}

        assert s.get_instruction(("9", "8")) is None


class TestSpecificityScoring:
    """
    Tests the logic:
    1. Fewer variables = Better (Literals are best).
    2. If total vars equal, fewer UNIQUE vars = Better (Specific constraints are best).
    """

    def test_literal_vs_variable(self):
        s = State("conflict")
        i_literal = make_instr("literal_winner")
        i_var = make_instr("variable_loser")

        # Rule 1: ('A', 'A') - Score: (0 vars, 0 unique) -> Best
        s.add_instruction(("A", "A"), i_literal)
        # Rule 2: ('A', $x)  - Score: (1 var, 1 unique)  -> Worse
        s.add_instruction(("A", "$x"), i_var)

        instr, _ = s.get_instruction(("A", "A"))
        assert instr.next_state.name == "literal_winner"

    def test_unique_variable_tiebreaker(self):
        s = State("conflict")
        i_specific = make_instr("specific_winner")
        i_generic = make_instr("generic_loser")

        # Rule 1: ($x, $x) - Score: (2 vars, 1 unique) -> Better (More constraints)
        s.add_instruction(("$x", "$x"), i_specific)
        # Rule 2: ($x, $y) - Score: (2 vars, 2 unique) -> Worse (Anything goes)
        s.add_instruction(("$x", "$y"), i_generic)

        # Input '7', '7' matches both, but ($x, $x) is more specific
        instr, bindings = s.get_instruction(("7", "7"))
        assert instr.next_state.name == "specific_winner"
        assert bindings["$x"] == "7"

    def test_variable_write_back(self):
        from varphi_python.lib.model import TuringMachine, Tape

        s = State("start")
        # Read $x, Write $x (echo)
        instr = Instruction(
            next_state=State("end"),
            write_symbols=("$x",),
            shift_directions=("STAY",),
            line_number=1,
        )
        s.add_instruction(("$x",), instr)

        tm = TuringMachine(1, (Tape("Q"),), s)

        assert tm.peek() is True
        tm.step()

        # Head should still be at 0, containing 'Q' (wrote 'Q' back)
        assert tm.tapes[0][0] == "Q"
        assert tm.state.name == "end"

    def test_degrees_of_freedom_priority(self):
        s = State("conflict")
        i_equality_heavy = make_instr("equality_winner")
        i_literal_mixed = make_instr("mixed_loser")

        # Rule A: ($x, $x, $x) -> Score: (Unique=1, Total=3)
        s.add_instruction(("$x", "$x", "$x"), i_equality_heavy)
        
        # Rule B: ($x, $y, A) -> Score: (Unique=2, Total=2)
        s.add_instruction(("$x", "$y", "A"), i_literal_mixed)

        # Input: (A, A, A) matches both rules.
        instr, bindings = s.get_instruction(("A", "A", "A"))
        
        assert instr.next_state.name == "equality_winner"
        assert bindings == {"$x": "A"}
