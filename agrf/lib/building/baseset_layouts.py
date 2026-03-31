"""
Defines base-set layouts using the sprites from baseset_sprites.
"""

from agrf.lib.building.layout import ALayout
from agrf.lib.building.baseset_sprites import default_grassland, default_railroad, building_ground
from agrf.lib.building.symmetry import BuildingSymmetrical, BuildingCylindrical

grassland_tile = BuildingCylindrical.memoize(ALayout(default_grassland, [], False))
railroad_tile = BuildingSymmetrical.memoize(ALayout(default_railroad, [], True))
building_ground_tile = BuildingCylindrical.memoize(ALayout(building_ground, [], False))
