import grf
from agrf.graphics import LayeredImage
from agrf.graphics.spritesheet import LazyAlternativeSprites


THIS_FILE = grf.PythonFile(__file__)


class MapSprite(grf.Sprite):
    def __init__(self, a, f, name, xofs=0, yofs=0):
        super().__init__(a.w, a.h, zoom=a.zoom, xofs=a.xofs + xofs, yofs=a.yofs + yofs, bpp=a.bpp, crop=a.crop)
        self.a = a
        self.f = f
        self._fname = name

    def get_fingerprint(self):
        return {"a": self.a.get_fingerprint(), "name": self._fname}

    def get_resource_files(self):
        return self.a.get_resource_files() + (THIS_FILE,)

    def get_data_layers(self, context):
        timer = context.start_timer()
        fa = self.f(LayeredImage.from_sprite(self.a).copy())
        timer.count_composing()

        return fa.w, fa.h, fa.rgb, fa.alpha, fa.mask
