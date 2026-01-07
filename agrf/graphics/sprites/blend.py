import grf
from agrf.graphics import LayeredImage
from agrf.graphics.spritesheet import LazyAlternativeSprites


THIS_FILE = grf.PythonFile(__file__)


class BlendSprite(grf.Sprite):
    def __init__(self, a, b, b_alpha=255):
        super().__init__(a.w, a.h, zoom=a.zoom, xofs=a.xofs, yofs=a.yofs, bpp=a.bpp, crop=a.crop)
        self.a = a
        self.b = b
        self.b_alpha = b_alpha

    def get_fingerprint(self):
        return {"a": self.a.get_fingerprint(), "b": self.b.get_fingerprint()}

    def get_resource_files(self):
        return self.a.get_resource_files() + self.b.get_resource_files() + (THIS_FILE,)

    def get_data_layers(self, context):
        timer = context.start_timer()
        a = LayeredImage.from_sprite(self.a).copy()
        b = LayeredImage.from_sprite(self.b).copy()
        a.blend_over(b, self.b_alpha)
        timer.count_composing()

        self.xofs = a.xofs
        self.yofs = a.yofs

        return a.w, a.h, a.rgb, a.alpha, a.mask
