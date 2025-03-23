import grf
from agrf.graphics import SCALE_TO_ZOOM
from agrf.graphics.sprites.map import MapSprite


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

    return grf.AlternativeSprites(*alts)
