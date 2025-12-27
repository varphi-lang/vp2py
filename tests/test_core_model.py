from varphi_python.lib import Tape, Head, TuringMachine, State
from varphi_devkit import BLANK, LEFT, RIGHT, STAY

class TestTape:
    def test_tape_initialization(self):
        t = Tape(['a', 'b', 'c'])
        assert t[0] == 'a'
        assert t[1] == 'b'
        assert t[2] == 'c'
        assert t[3] == BLANK
        assert t[-1] == BLANK
        assert t[100] == BLANK  # Test default value
        assert t[-100] == BLANK

    def test_tape_dynamic_growth(self):
        t = Tape([])
        t[5] = 'x'
        assert t.to_string() == 'x'
        
        t[-2] = 'y'
        # Range is now -2 to 5. -2='y', -1=_, 0=_, 1=_, 2=_, 3=_, 4=_, 5='x'
        # Total string length 8
        assert t[-2] == 'y'
        assert t[0] == BLANK
        assert len(t.to_string()) == 8

    def test_tape_updates_bounds(self):
        t = Tape(['a'])
        assert t._min_idx == 0
        assert t._max_idx == 0
        
        t[10] = 'z'
        assert t._max_idx == 10
        
        t[-5] = 'start'
        assert t._min_idx == -5

class TestHead:
    def test_head_movement(self):
        t = Tape(['a', 'b'])
        h = Head(t)
        assert h.index == 0
        assert h.read() == 'a'
        
        h.move(RIGHT)
        assert h.index == 1
        assert h.read() == 'b'
        
        h.move(LEFT)
        assert h.index == 0
        
        h.move(STAY)
        assert h.index == 0

    def test_space_complexity_tracking(self):
        t = Tape(['1', '2', '3'])
        h = Head(t)
        
        # Reading user-input shouldn't increase complexity
        h.read()
        assert h.space_complexity() == 0
        
        # Moving outside initial bounds
        h.move(RIGHT) # 1
        h.move(RIGHT) # 2
        h.move(RIGHT) # 3 (New cell!)
        h.read()      # Accessing it
        assert h.space_complexity() == 1
        
        # Moving left past 0
        h.index = -1
        h.write('x')
        assert h.space_complexity() == 2

class TestMachineBasics:
    def test_halt_condition(self):
        # A machine with no rules should halt immediately
        s1 = State("start")
        tm = TuringMachine(1, (Tape(['a']),), s1)
        
        assert tm.peek() is False
        assert tm._next_instruction is None