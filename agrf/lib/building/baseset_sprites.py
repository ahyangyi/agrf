"""
Defines base-set sprites.

Each refers to a fixed sprite ID, but the actual look can vary across climates, base sets or NewGRFs.
"""

from agrf.lib.building.layout import ADefaultGroundSprite
from agrf.lib.building.registers import Registers

default_grassland = ADefaultGroundSprite(3981, flags={"add": Registers.CLIMATE_OFFSET})

default_railroad = ADefaultGroundSprite(1011, flags={"add": Registers.CLIMATE_RAIL_OFFSET})
default_railroad_y = ADefaultGroundSprite(1012, flags={"add": Registers.CLIMATE_RAIL_OFFSET})
