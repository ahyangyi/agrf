from functools import cache
from dataclasses import dataclass, replace
from dataclass_type_validator import dataclass_type_validator
from agrf.graphics import LayeredImage
from agrf.utils import unique_tuple
from agrf.lib.building.layout import ALayout, RenderContext


DEFAULT_RENDER_CONTEXT = RenderContext()


@dataclass
class Demo:
    tiles: list
    title: str = ""
    remap: object = None
    climate: str = "temperate"
    subclimate: str = "default"
    rail_type: str = "default"
    merge_bbox: bool = False
    altitude: object = None
    render_contexts: list | None = None
    _smart_render_contexts: list = None

    def __post_init__(self):
        self._smart_render_contexts = self.infer_render_contexts()
        dataclass_type_validator(self)

    def infer_render_contexts(self):
        ret = []
        for i, row in enumerate(self.tiles):
            ret_row = []
            for j, tile in enumerate(row):
                if self.render_contexts is not None:
                    rc = self.render_contexts[i][j]
                else:
                    rc = DEFAULT_RENDER_CONTEXT
                ret_row.append(
                    RenderContext(
                        climate=rc.climate or self.climate,
                        subclimate=rc.subclimate or self.subclimate,
                        rail_type=rc.rail_type or self.rail_type,
                    )
                )
            ret.append(ret_row)
        return ret

    @property
    def max_altitude(self):
        if self.altitude is None:
            return 0
        return max(
            self.point_altitude(row, column)
            for row in range(len(self.tiles) + 1)
            for column in range(len(self.tiles[0]) + 1)
        )

    def point_altitude(self, row, column):
        if self.altitude is None:
            return 0
        return self.altitude[row][column]

    def tile_altitude(self, row, column):
        if self.altitude is None:
            return 0
        return min(self.altitude[r][c] for r in [row, row + 1] for c in [column, column + 1])

    def tile_slope(self, row, column):
        if self.altitude is None:
            return 0
        min_altitude = min(self.altitude[r][c] for r in [row, row + 1] for c in [column, column + 1])
        west = self.altitude[row][column] - min_altitude
        south = self.altitude[row + 1][column] - min_altitude
        east = self.altitude[row + 1][column + 1] - min_altitude
        north = self.altitude[row][column + 1] - min_altitude
        steep = int(max(west, south, east, north) > 1)
        west = min(west, 1)
        south = min(south, 1)
        east = min(east, 1)
        north = min(north, 1)
        return west + south * 2 + east * 4 + north * 8 + steep * 16

    def to_layout(self):
        sprites = []
        rows = len(self.tiles)
        columns = len(self.tiles[0])
        for r, row in enumerate(self.tiles):
            for c, sprite in enumerate(row[::-1]):
                if sprite is not None:
                    tile_slope = self.tile_slope(r, len(row) - 1 - c)
                    sprite = sprite.enable_foundation(tile_slope)
                    sprites.extend(
                        sprite.demo_filter(self._smart_render_contexts[r][len(row) - 1 - c])
                        .demo_translate(c * 16 - (columns - 1) * 8, r * 16 - (rows - 1) * 8, self.tile_altitude(r, c))
                        .parent_sprites
                    )
        return ALayout(None, sprites, False)

    def graphics(self, scale, bpp, remap=None):
        try:
            max_altitude = self.max_altitude
            remap = remap or self.remap
            if self.merge_bbox:
                return self.to_layout().graphics(
                    scale,
                    bpp,
                    remap,
                    render_context=RenderContext(
                        climate=self.climate, subclimate=self.subclimate, rail_type=self.rail_type
                    ),
                )
            yofs = 32 * scale
            img = LayeredImage.canvas(
                -16 * scale * (len(self.tiles) + len(self.tiles[0])),
                -yofs,
                32 * scale * (len(self.tiles) + len(self.tiles[0])),
                yofs + 16 * scale * (len(self.tiles) + len(self.tiles[0])),
                has_mask=remap is None,
            )

            for r, row in enumerate(self.tiles):
                for c, sprite in enumerate(row[::-1]):
                    if sprite is None:
                        continue
                    subimg = sprite.graphics(
                        scale, bpp, remap=remap, render_context=self._smart_render_contexts[r][len(row) - 1 - c]
                    )
                    img.blend_over(
                        subimg.move((32 * r - 32 * c) * scale, (16 * r + 16 * c - 8 * self.tile_altitude(r, c)) * scale)
                    )
            return img
        except Exception as e:
            # Error message is generally particularly hard to understand when something goes wrong here
            # Hence, we always print the demo title when an exception happens
            print(f"Caught exception during demo graphics generation: {self.title}")
            raise

    @property
    def T(self):
        assert self.render_contexts is None
        return replace(self, tiles=[[tile and tile.T for tile in row] for row in self.tiles[::-1]])

    @property
    def M(self):
        assert self.render_contexts is None
        return replace(self, tiles=[[tile and tile.M for tile in row[::-1]] for row in list(zip(*self.tiles))[::-1]])

    def get_fingerprint(self):
        return {"tiles": [[x and x.get_fingerprint() for x in row] for row in self.tiles], "remap": "FIXME"}  # FIXME

    def get_resource_files(self):
        return unique_tuple(f for row in self.tiles for x in row for f in x.get_resource_files())
