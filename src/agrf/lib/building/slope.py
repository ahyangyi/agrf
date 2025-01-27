from dataclasses import dataclass
from .symmetry import BuildingSymmetricalY, BuildingDiamond, BuildingCylindrical, BuildingDiagonalAlt, BuildingDiagonal


@dataclass
class SlopeType:
    value: int


slope_types = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 23, 27, 29, 30]

flat = BuildingCylindrical.create_variants([SlopeType(0)])
ortho = BuildingSymmetricalY.create_variants([SlopeType(3), SlopeType(6), SlopeType(12), SlopeType(9)])
para = BuildingDiamond.create_variants([SlopeType(5), SlopeType(10)])
mono = BuildingDiagonalAlt.create_variants([SlopeType(1), SlopeType(4), SlopeType(8), SlopeType(2)])
tri = BuildingDiagonal.create_variants([SlopeType(7), SlopeType(14), SlopeType(11), SlopeType(13)])
steep = BuildingDiagonal.create_variants([SlopeType(23), SlopeType(30), SlopeType(27), SlopeType(29)])


def make_slopes(sprites, sym):
    ret = {i: {} for i in sym.render_indices()}

    for slopeGroup in [flat, ortho, para, mono, tri, steep]:
        for slopeIndex, slopeType in zip(slopeGroup.render_indices(), slopeGroup.all_variants):
            for i in sym.render_indices():
                for slopeIndex2, slopeType2 in zip(slopeGroup.render_indices(), slopeGroup.all_variants):
                    if (
                        slopeType._symmetry_descriptor[slopeType.compose_symmetry_indices(slopeIndex2, i)]
                        == slopeType._symmetry_descriptor[slopeIndex]
                    ):
                        ret[i][slopeType.value] = sprites[slopeType2.value].symmetry_index(i)
                        break
    return ret
