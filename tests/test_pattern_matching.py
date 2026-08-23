import pytest
from vp2py.lib.model import State, Tape, TuringMachine
from varphi_devkit import Direction, Variable, Character, VarphiTransition


def make_transition(
    read_symbols: tuple,
    write_symbols: tuple = None,
    next_state: str = "end",
    current_state: str = "test",
) -> VarphiTransition:
    """Helper to mock a VarphiTransition with valid defaults for testing."""
    if write_symbols is None:
        write_symbols = tuple(Character("w") for _ in read_symbols)

    # Notice we don't pass `specificity` because __post_init__ handles it automatically!
    return VarphiTransition(
        current_state=current_state,
        read_symbols=read_symbols,
        next_state=next_state,
        write_symbols=write_symbols,
        shift_directions=tuple(Direction.STAY for _ in read_symbols),
        line_number=1,
    )


class TestPatternMatching:
    def test_literal_match(self):
        s = State("test")
        s.add_transition(make_transition((Character("A"), Character("B"))))

        trans, bindings = s.get_transition((Character("A"), Character("B")))
        assert trans is not None
        assert bindings == {}

        assert s.get_transition((Character("A"), Character("C"))) is None

    def test_variable_binding_success(self):
        s = State("test")
        s.add_transition(make_transition((Variable(0), Character("B"))))

        trans, bindings = s.get_transition((Character("Z"), Character("B")))
        assert trans is not None
        assert bindings == {Variable(0): Character("Z")}

    def test_variable_consistency_constraint(self):
        s = State("test")
        s.add_transition(make_transition((Variable(0), Variable(0))))

        trans, bindings = s.get_transition((Character("9"), Character("9")))
        assert trans is not None
        assert bindings == {Variable(0): Character("9")}

        assert s.get_transition((Character("9"), Character("8"))) is None


class TestSpecificityScoring:
    """
    Tests the logic:
    1. Fewer variables = Better (Literals are best).
    2. If total vars equal, fewer UNIQUE vars = Better (Specific constraints are best).
    """

    def test_literal_vs_variable(self):
        s = State("conflict")

        # Rule 1: ('A', 'A') - Score: (0 vars, 0 unique) -> Best
        t_literal = make_transition(
            (Character("A"), Character("A")), next_state="literal_winner"
        )
        # Rule 2: ('A', $x)  - Score: (1 var, 1 unique)  -> Worse
        t_var = make_transition(
            (Character("A"), Variable(0)), next_state="variable_loser"
        )

        s.add_transition(t_literal)
        s.add_transition(t_var)

        # Simulate the Devkit's pre-compilation sorting required by the early-exit loop
        s.transitions.sort(key=lambda t: t.specificity)

        trans, _ = s.get_transition((Character("A"), Character("A")))
        assert trans.next_state == "literal_winner"

    def test_unique_variable_tiebreaker(self):
        s = State("conflict")

        # Rule 1: ($x, $x) - Score: (2 vars, 1 unique) -> Better (More constraints)
        t_specific = make_transition(
            (Variable(0), Variable(0)), next_state="specific_winner"
        )
        # Rule 2: ($x, $y) - Score: (2 vars, 2 unique) -> Worse (Anything goes)
        t_generic = make_transition(
            (Variable(0), Variable(1)), next_state="generic_loser"
        )

        s.add_transition(t_specific)
        s.add_transition(t_generic)
        s.transitions.sort(key=lambda t: t.specificity)

        trans, bindings = s.get_transition((Character("7"), Character("7")))
        assert trans.next_state == "specific_winner"
        assert bindings[Variable(0)] == Character("7")

    def test_degrees_of_freedom_priority(self):
        s = State("conflict")

        # Rule A: ($x, $x, $x) -> Score: (Unique=1, Total=3)
        t_equality_heavy = make_transition(
            (Variable(0), Variable(0), Variable(0)), next_state="equality_winner"
        )
        # Rule B: ($x, $y, A) -> Score: (Unique=2, Total=2)
        t_literal_mixed = make_transition(
            (Variable(0), Variable(1), Character("A")), next_state="mixed_loser"
        )

        s.add_transition(t_equality_heavy)
        s.add_transition(t_literal_mixed)
        s.transitions.sort(key=lambda t: t.specificity)

        trans, bindings = s.get_transition(
            (Character("A"), Character("A"), Character("A"))
        )

        assert trans.next_state == "equality_winner"
        assert bindings == {Variable(0): Character("A")}

    def test_variable_write_back(self):
        s = State("start")
        end_state = State("end")
        registry = {"start": s, "end": end_state}

        trans = make_transition(
            read_symbols=(Variable(0),), write_symbols=(Variable(0),), next_state="end"
        )
        s.add_transition(trans)

        tm = TuringMachine(
            k=1,
            tapes=(Tape([Character("Q")]),),
            initial_state=s,
            state_registry=registry,
        )

        assert tm.peek() is True
        tm.step()

        # Head should still be at 0, containing 'Q' (wrote 'Q' back)
        assert tm.tapes[0][0] == Character("Q")
        assert tm.state.name == "end"
