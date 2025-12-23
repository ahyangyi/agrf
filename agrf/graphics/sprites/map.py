import grf
from agrf.graphics import LayeredImage
from agrf.graphics.spritesheet import LazyAlternativeSprites


THIS_FILE = grf.PythonFile(__file__)


class MapSprite(grf.Sprite):
    def __init__(self, a, f, name, xofs=0, yofs=0):
        if not isinstance(a, tuple):
            a = (a,)
        super().__init__(
            a[0].w, a[0].h, zoom=a[0].zoom, xofs=a[0].xofs + xofs, yofs=a[0].yofs + yofs, bpp=a[0].bpp, crop=a[0].crop
        )
        self.a = a
        self.f = f
        self._fname = name

    def get_fingerprint(self):
        return {"a": [x.get_fingerprint() for x in self.a], "name": self._fname}

    def get_resource_files(self):
        return sum((x.get_resource_files() for x in self.a), start=tuple()) + (THIS_FILE,)

    def get_data_layers(self, context):
        timer = context.start_timer()
        fa = self.f([LayeredImage.from_sprite(x).copy() for x in self.a])
        timer.count_composing()

        return fa.w, fa.h, fa.rgb, fa.alpha, fa.mask
