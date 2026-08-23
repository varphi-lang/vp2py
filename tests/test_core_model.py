from vp2py.lib.model import Tape, Head, TuringMachine, State
from varphi_devkit import Direction, BuiltinSymbol, Character


class TestTape:
    def test_tape_initialization(self):
        t = Tape([Character("a"), Character("b"), Character("c")])
        assert t[0] == Character("a")
        assert t[1] == Character("b")
        assert t[2] == Character("c")
        assert t[3] == BuiltinSymbol.BLANK
        assert t[-1] == BuiltinSymbol.BLANK
        assert t[100] == BuiltinSymbol.BLANK
        assert t[-100] == BuiltinSymbol.BLANK

    def test_tape_dynamic_growth(self):
        t = Tape([])
        t[5] = Character("x")
        assert t.to_string("_") == "x"

        t[-2] = Character("y")
        # Range is now -2 to 5. -2='y', -1=_, 0=_, 1=_, 2=_, 3=_, 4=_, 5='x'
        # Total string length 8
        assert t[-2] == Character("y")
        assert t[0] == BuiltinSymbol.BLANK
        assert len(t.to_string("_")) == 8

    def test_tape_updates_bounds(self):
        t = Tape([Character("a")])
        assert t._min_idx == 0
        assert t._max_idx == 0

        t[10] = Character("z")
        assert t._max_idx == 10

        t[-5] = Character("s")
        assert t._min_idx == -5


class TestHead:
    def test_head_movement(self):
        t = Tape([Character("a"), Character("b")])
        h = Head(t)
        assert h.index == 0
        assert h.read() == Character("a")

        h.move(Direction.RIGHT)
        assert h.index == 1
        assert h.read() == Character("b")

        h.move(Direction.LEFT)
        assert h.index == 0

        h.move(Direction.STAY)
        assert h.index == 0

    def test_space_complexity_tracking(self):
        t = Tape([Character("1"), Character("2"), Character("3")])
        h = Head(t)

        # Reading user-input shouldn't increase complexity
        h.read()
        assert h.space_complexity() == 0

        # Moving outside initial bounds
        h.move(Direction.RIGHT)  # 1
        h.move(Direction.RIGHT)  # 2
        h.move(Direction.RIGHT)  # 3 (New cell!)
        h.read()  # Accessing it
        assert h.space_complexity() == 1

        # Moving Direction.LEFT past 0
        h.index = -1
        h.write(Character("x"))
        assert h.space_complexity() == 2


class TestMachineBasics:
    def test_halt_condition(self):
        # A machine with no rules should halt immediately
        s1 = State("start")
        registry = {"start": s1}
        tm = TuringMachine(
            k=1,
            tapes=(Tape([Character("a")]),),
            initial_state=s1,
            state_registry=registry,
        )

        assert tm.peek() is False
        assert tm._next_transition is None
