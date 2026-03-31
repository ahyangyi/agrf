"""
Defines base-set sprites.

Each refers to a fixed sprite ID, but the actual look can vary across climates, base sets or NewGRFs.
"""

from agrf.lib.building.layout import ADefaultGroundSprite
from agrf.lib.building.registers import Registers
from agrf.lib.building.symmetry import BuildingSymmetrical, BuildingCylindrical

default_grassland = BuildingCylindrical.memoize(ADefaultGroundSprite(3981, flags={"add": Registers.CLIMATE_OFFSET}))
default_railroad = BuildingSymmetrical.memoize(ADefaultGroundSprite(1012, flags={"add": Registers.CLIMATE_RAIL_OFFSET}))
building_ground = BuildingCylindrical.memoize(ADefaultGroundSprite(1420, flags={"add": Registers.ZERO}))
