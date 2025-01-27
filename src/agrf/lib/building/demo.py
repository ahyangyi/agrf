from dataclasses import dataclass, replace
from agrf.graphics import LayeredImage
from agrf.utils import unique_tuple
from agrf.lib.building.layout import ALayout


@dataclass
class Demo:
    tiles: list
    title: str = ""
    remap: object = None
    climate: str = "temperate"
    subclimate: str = "default"
    merge_bbox: bool = False

    def to_layout(self):
        sprites = []
        rows = len(self.tiles)
        columns = len(self.tiles[0])
        for r, row in enumerate(self.tiles):
            for c, sprite in enumerate(row[::-1]):
                if sprite is not None:
                    sprites.extend(
                        sprite.demo_translate(c * 16 - (columns - 1) * 8, r * 16 - (rows - 1) * 8).parent_sprites
                    )
        return ALayout(None, sprites, False)

    def graphics(self, scale, bpp, remap=None):
        remap = remap or self.remap
        if self.merge_bbox:
            return self.to_layout().graphics(scale, bpp, remap, climate=self.climate, subclimate=self.subclimate)
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
                subimg = sprite.graphics(scale, bpp, remap=remap, climate=self.climate, subclimate=self.subclimate)
                img.blend_over(subimg.move((32 * r - 32 * c) * scale, (16 * r + 16 * c) * scale))
        return img

    @property
    def T(self):
        return replace(self, tiles=[[tile and tile.T for tile in row] for row in self.tiles[::-1]])

    @property
    def M(self):
        return replace(self, tiles=[[tile and tile.M for tile in row[::-1]] for row in list(zip(*self.tiles))[::-1]])

    def get_fingerprint(self):
        return {"tiles": [[x and x.get_fingerprint() for x in row] for row in self.tiles], "remap": "FIXME"}  # FIXME

    def get_resource_files(self):
        return unique_tuple(f for row in self.tiles for x in row for f in x.get_resource_files())
