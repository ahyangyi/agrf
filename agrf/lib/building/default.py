import grf
from agrf.lib.building.symmetry import BuildingCylindrical
from agrf.lib.building.layout import AGroundSprite
from agrf.lib.building.registers import Registers

empty_ground = BuildingCylindrical.create_variants([AGroundSprite(grf.EMPTY_SPRITE, flags={"add": Registers.ZERO})])
