import grf
from agrf.lib.building.station_tile_switch import make_horizontal_switch, make_vertical_switch


def switch_set(s):
    if isinstance(s, int):
        return set()
    return set([id(s)] + [x for r in s._ranges for x in switch_set(r.ref)] + list(switch_set(s.default)))


class MockValue:
    def __init__(self, v):
        self.v = v

    @property
    def T(self):
        return MockValue(self.v ^ 2)

    @property
    def R(self):
        return MockValue(self.v ^ 1)

    def lookup(self, w, h, x, y, t):
        return self.v


def test_horizontal_switch():
    a = make_horizontal_switch(lambda l, r: MockValue(l * 0x100 + r * 0x10))
    assert 0x30 == a.lookup(4, 4, 0, 0)
    assert 0x120 == a.lookup(4, 4, 1, 0)
    assert 0x32 == a.T.lookup(4, 4, 0, 0)
    assert 0x301 == a.R.lookup(4, 4, 0, 0)


def test_vertical_switch():
    a = make_vertical_switch(lambda t, d: MockValue(t * 0x100 + d * 0x10))
    assert 0x30 == a.lookup(4, 4, 0, 0, 0)
    assert 0x120 == a.lookup(4, 4, 0, 1, 0)
    assert 0x302 == a.T.lookup(4, 4, 0, 0, 0)
    assert 0x31 == a.R.lookup(4, 4, 0, 0, 0)


def test_switch_compression_1():
    a = make_horizontal_switch(lambda l, r: l).to_index()
    assert isinstance(a, grf.Switch)
    assert len(a._ranges) == 15
    assert all(isinstance(v.ref, int) for v in a._ranges)
    assert len(switch_set(a)) == 1


def test_switch_compression_2():
    a = make_horizontal_switch(lambda l, r: r).to_index()
    assert isinstance(a, grf.Switch)
    assert len(a._ranges) == 15
    assert all(isinstance(v.ref, int) for v in a._ranges)
    assert len(switch_set(a)) == 1


def test_switch_compression_3():
    a = make_horizontal_switch(lambda l, r: l ^ r).to_index()
    assert isinstance(a, grf.Switch)
    assert len(a._ranges) == 15
    assert all(isinstance(v.ref, grf.Switch) for v in a._ranges)
    assert len(switch_set(a)) == 17


def test_switch_compression_4():
    a = make_horizontal_switch(lambda l, r: int(l == 7)).to_index()
    assert isinstance(a, grf.Switch)
    assert len(a._ranges) == 1
    assert all(isinstance(v.ref, int) for v in a._ranges)
    assert len(switch_set(a)) == 1


def test_switch_compression_5():
    a = make_horizontal_switch(lambda l, r: int(r == 7)).to_index()
    assert isinstance(a, grf.Switch)
    assert len(a._ranges) == 1
    assert all(isinstance(v.ref, int) for v in a._ranges)
    assert len(switch_set(a)) == 1


def test_switch_compression_6():
    a = make_horizontal_switch(lambda l, r: int((l == 7) ^ (r == 7))).to_index()
    assert isinstance(a, grf.Switch)
    assert len(a._ranges) == 1
    assert all(isinstance(v.ref, grf.Switch) for v in a._ranges)
    assert all(len(v.ref._ranges) == 1 for v in a._ranges)
    assert len(switch_set(a)) == 3


def test_switch_compression_7():
    a = make_horizontal_switch(lambda l, r: int(l == 7 or r == 7)).to_index()
    assert isinstance(a, grf.Switch)
    assert len(a._ranges) == 1
    assert len(switch_set(a)) == 2


def test_switch_compression_8():
    a = make_horizontal_switch(lambda l, r: int(3 <= l <= 13)).to_index()
    assert isinstance(a, grf.Switch)
    assert len(a._ranges) == 1
    assert all(isinstance(v.ref, int) for v in a._ranges)
    assert len(switch_set(a)) == 1


def test_switch_compression_9():
    a = make_horizontal_switch(lambda l, r: int(3 <= r <= 13)).to_index()
    assert isinstance(a, grf.Switch)
    assert len(a._ranges) == 1
    assert all(isinstance(v.ref, int) for v in a._ranges)
    assert len(switch_set(a)) == 1


def test_switch_compression_10():
    a = make_horizontal_switch(lambda l, r: int((3 <= l <= 13) ^ (3 <= r <= 13))).to_index()
    assert isinstance(a, grf.Switch)
    assert len(a._ranges) == 1
    assert all(isinstance(v.ref, grf.Switch) for v in a._ranges)
    assert all(len(v.ref._ranges) == 1 for v in a._ranges)
    assert len(switch_set(a)) == 3
