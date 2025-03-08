import grf
from agrf.graphics import SCALE_TO_ZOOM
from agrf.graphics.sprites.foundation import FoundationSprite


def make_foundations(sprite):
    sprite.voxel.render()  # FIXME agrf cannot correctly track dependencies here
    ret = []
    for i in range(8):
        alts = []
        for scale in [1, 2, 4]:
            for bpp in [32]:
                if (s := sprite.get_sprite(zoom=SCALE_TO_ZOOM[scale], bpp=bpp)) is not None:
                    fs = FoundationSprite(s, i)
                    alts.append(fs)

        ret.append(grf.AlternativeSprites(*alts))
    return ret
