"""
Defines base-set layouts using the sprites from baseset_sprites.
"""

from agrf.lib.building.layout import ALayout
from agrf.lib.building.baseset_sprites import default_grassland, default_railroad, default_railroad_y

grassland_tile = ALayout(default_grassland, [], False)
railroad_tile = ALayout(default_railroad, [], True)
railroad_y_tile = ALayout(default_railroad_y, [], True)
