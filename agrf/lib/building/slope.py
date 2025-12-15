from dataclasses import dataclass
from dataclass_type_validator import dataclass_type_validator
from .symmetry import BuildingSymmetricalY, BuildingDiamond, BuildingCylindrical, BuildingDiagonalAlt, BuildingDiagonal


@dataclass
class SlopeType:
    value: int
    offset: int = None

    def __post_init__(self):
        self.offset = {29: 15, 23: 16, 27: 17, 30: 18}.get(self.value, self.value)
        dataclass_type_validator(self)


flat = BuildingCylindrical.create_variants([SlopeType(0)])
ortho = BuildingSymmetricalY.create_variants([SlopeType(3), SlopeType(6), SlopeType(12), SlopeType(9)])
para = BuildingDiamond.create_variants([SlopeType(5), SlopeType(10)])
mono = BuildingDiagonalAlt.create_variants([SlopeType(1), SlopeType(4), SlopeType(8), SlopeType(2)])
tri = BuildingDiagonal.create_variants([SlopeType(7), SlopeType(14), SlopeType(11), SlopeType(13)])
steep = BuildingDiagonal.create_variants([SlopeType(23), SlopeType(30), SlopeType(27), SlopeType(29)])

slope_groups = [flat, ortho, para, mono, tri, steep]
slope_types = [t for g in slope_groups for t in g.all_variants]


def make_slopes(sprites, sym):
    ret = {i: {} for i in sym.render_indices()}

    for slopeGroup in slope_groups:
        for slopeIndex, slopeType in zip(slopeGroup.render_indices(), slopeGroup.all_variants):
            for i in sym.render_indices():
                for slopeIndex2, slopeType2 in zip(slopeGroup.render_indices(), slopeGroup.all_variants):
                    if (
                        slopeType._symmetry_descriptor[slopeType.compose_symmetry_indices(slopeIndex2, i)]
                        == slopeType._symmetry_descriptor[slopeIndex]
                    ):
                        ret[i][slopeType.value] = sprites[slopeType2.value].symmetry_item(i)
                        break

    for k, v in ret.items():
        for s in v.values():
            s.slope_variants = v

    return ret
