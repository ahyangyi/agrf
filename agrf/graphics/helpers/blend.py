import grf
from agrf.graphics import SCALE_TO_ZOOM
from agrf.graphics.sprites.blend import BlendSprite


def blend_alternative_sprites(a, b):
    alts = []
    for scale in [1, 2, 4]:
        for bpp in [8, 32]:
            if (sa := a.get_sprite(zoom=SCALE_TO_ZOOM[scale], bpp=bpp)) is None:
                continue
            if (sb := b.get_sprite(zoom=SCALE_TO_ZOOM[scale], bpp=bpp)) is None:
                continue
            fs = BlendSprite(sa, sb)
            alts.append(fs)
    assert len(alts) > 0

    return grf.AlternativeSprites(*alts)
