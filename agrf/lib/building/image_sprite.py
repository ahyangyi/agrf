import grf
from agrf.graphics import SCALE_TO_ZOOM


def image_sprite(path, y=127, crop=True, child=False):
    return grf.AlternativeSprites(
        grf.FileSprite(
            grf.ImageFile(path),
            0,
            0,
            256,
            y,
            xofs=0 if child else -124,
            yofs=127 - y,
            bpp=32,
            zoom=SCALE_TO_ZOOM[4],
            crop=crop,
        )
    )
