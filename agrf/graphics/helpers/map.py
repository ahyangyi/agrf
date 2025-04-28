import grf
from agrf.graphics import SCALE_TO_ZOOM
from agrf.graphics.sprites.map import MapSprite


class MapAlternativeSprites(grf.AlternativeSprites):
    def __init__(self, name, source, *sprites):
        super().__init__(*sprites)
        self.name = name
        self.source = source

    def get_fingerprint(self):
        return {"map-name": self.name, "source": self.source.get_fingerprint()}


def map_alternative_sprites(a, f, name, xofs=0, yofs=0):
    alts = []
    for scale in [1, 2, 4]:
        for bpp in [8, 32]:
            if (sa := a.get_sprite(zoom=SCALE_TO_ZOOM[scale], bpp=bpp)) is None:
                continue
            fs = MapSprite(
                sa, lambda x, scale=scale, bpp=bpp: f(x, scale, bpp), name, xofs=xofs * scale, yofs=yofs * scale
            )
            alts.append(fs)

    return MapAlternativeSprites(name, a, *alts)
