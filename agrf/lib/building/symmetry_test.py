from symmetry import (
    BuildingFull,
    BuildingSymmetrical,
    BuildingSymmetricalX,
    BuildingSymmetricalY,
    BuildingRotational,
    BuildingDiagonal,
    BuildingDiamond,
    BuildingCylindrical,
)


def test_identity():
    symmetries = [
        BuildingFull,
        BuildingSymmetrical,
        BuildingSymmetricalX,
        BuildingSymmetricalY,
        BuildingRotational,
        BuildingDiagonal,
        BuildingDiamond,
        BuildingCylindrical,
    ]

    for i in range(len(symmetries)):
        for j in range(i + 1, len(symmetries)):
            assert symmetries[i] is not symmetries[j]


def test_is_symmetrical_y():
    assert not BuildingFull.is_symmetrical_y()
    assert BuildingSymmetrical.is_symmetrical_y()
    assert not BuildingSymmetricalX.is_symmetrical_y()
    assert BuildingSymmetricalY.is_symmetrical_y()
    assert not BuildingRotational.is_symmetrical_y()
    assert not BuildingDiagonal.is_symmetrical_y()
    assert not BuildingDiamond.is_symmetrical_y()
    assert BuildingCylindrical.is_symmetrical_y()


def test_break_x_symmetry():
    assert BuildingFull.break_x_symmetry() is BuildingFull
    assert BuildingSymmetrical.break_x_symmetry() is BuildingSymmetricalY
    assert BuildingSymmetricalX.break_x_symmetry() is BuildingFull
    assert BuildingSymmetricalY.break_x_symmetry() is BuildingSymmetricalY
    assert BuildingRotational.break_x_symmetry() is BuildingFull
    assert BuildingDiagonal.break_x_symmetry() is BuildingFull
    assert BuildingDiamond.break_x_symmetry() is BuildingFull
    assert BuildingCylindrical.break_x_symmetry() is BuildingSymmetricalY


def test_break_y_symmetry():
    assert BuildingFull.break_y_symmetry() is BuildingFull
    assert BuildingSymmetrical.break_y_symmetry() is BuildingSymmetricalX
    assert BuildingSymmetricalX.break_y_symmetry() is BuildingSymmetricalX
    assert BuildingSymmetricalY.break_y_symmetry() is BuildingFull
    assert BuildingRotational.break_y_symmetry() is BuildingFull
    assert BuildingDiagonal.break_y_symmetry() is BuildingFull
    assert BuildingDiamond.break_y_symmetry() is BuildingFull
    assert BuildingCylindrical.break_y_symmetry() is BuildingSymmetricalX


def test_add_x_symmetry():
    assert BuildingFull.add_x_symmetry() is BuildingSymmetricalX
    assert BuildingSymmetrical.add_x_symmetry() is BuildingSymmetrical
    assert BuildingSymmetricalX.add_x_symmetry() is BuildingSymmetricalX
    assert BuildingSymmetricalY.add_x_symmetry() is BuildingSymmetrical
    assert BuildingRotational.add_x_symmetry() is BuildingSymmetrical
    assert BuildingDiagonal.add_x_symmetry() is BuildingCylindrical
    assert BuildingDiamond.add_x_symmetry() is BuildingCylindrical
    assert BuildingCylindrical.add_x_symmetry() is BuildingCylindrical


def test_add_y_symmetry():
    assert BuildingFull.add_y_symmetry() is BuildingSymmetricalY
    assert BuildingSymmetrical.add_y_symmetry() is BuildingSymmetrical
    assert BuildingSymmetricalX.add_y_symmetry() is BuildingSymmetrical
    assert BuildingSymmetricalY.add_y_symmetry() is BuildingSymmetricalY
    assert BuildingRotational.add_y_symmetry() is BuildingSymmetrical
    assert BuildingDiagonal.add_y_symmetry() is BuildingCylindrical
    assert BuildingDiamond.add_y_symmetry() is BuildingCylindrical
    assert BuildingCylindrical.add_y_symmetry() is BuildingCylindrical


def test_join():
    assert BuildingSymmetricalX.join(BuildingSymmetricalX) is BuildingSymmetricalX
    assert BuildingSymmetricalX.join(BuildingSymmetricalY) is BuildingFull
    assert BuildingRotational.join(BuildingDiamond) is BuildingRotational
    assert BuildingDiamond.join(BuildingDiagonal) is BuildingDiagonal
    assert BuildingDiamond.join(BuildingSymmetricalX) is BuildingFull


def test_chirality():
    assert BuildingDiagonal.chirality_indices() == [0]
