from dataclasses import dataclass
from symmetry import BuildingCylindrical, BuildingSymmetricalX, BuildingFull
from agrf.lib.building.slope import make_slopes, slope_types


@dataclass
class MockObject:
    debug_id: int


def test_cylindrical():
    sprites = {i.value: BuildingCylindrical.create_variants([MockObject(i.offset)]) for i in slope_types}
    ret = make_slopes(sprites, BuildingCylindrical)

    for i in slope_types:
        assert ret[0][i.value] is sprites[i.value]


def test_x():
    sprites = {
        i.value: BuildingSymmetricalX.create_variants([MockObject(i.offset * 4 + j) for j in range(4)])
        for i in slope_types
    }
    ret = make_slopes(sprites, BuildingSymmetricalX)

    for i in slope_types:
        assert ret[0][i.value] is sprites[i.value]
        for j in [1, 4, 5]:
            assert i.value in ret[j]
    assert ret[1][0] is sprites[0].M


def test_full():
    sprites = {
        i.value: BuildingFull.create_variants([MockObject(i.offset * 8 + j) for j in range(8)]) for i in slope_types
    }
    ret = make_slopes(sprites, BuildingFull)

    for i in slope_types:
        assert ret[0][i.value] is sprites[i.value]
        for j in range(1, 8):
            assert i.value in ret[j]
    assert ret[1][1] is sprites[4].M
    assert ret[2][3] is sprites[12].R
    assert ret[1][3] is sprites[6].M
    assert ret[1][7] is sprites[7].M
    assert ret[2][7] is sprites[14].R
    assert ret[3][7] is sprites[14].R.M
