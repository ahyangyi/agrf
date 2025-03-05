import grf
from agrf.graphics.cv.foundation import make_foundation
from agrf.graphics import LayeredImage, SCALE_TO_ZOOM, ZOOM_TO_SCALE
from agrf.graphics.spritesheet import LazyAlternativeSprites


THIS_FILE = grf.PythonFile(__file__)


class FoundationSprite(grf.Sprite):
    def __init__(self, base_sprite, foundation_id):
        super().__init__(
            base_sprite.w,
            base_sprite.h,
            zoom=base_sprite.zoom,
            xofs=base_sprite.xofs,
            yofs=base_sprite.yofs,
            bpp=base_sprite.bpp,
            crop=base_sprite.crop,
        )
        self.base_sprite = base_sprite
        self.foundation_id = foundation_id

    def get_fingerprint(self):
        return {"base_sprite": self.base_sprite.get_fingerprint()}

    def get_resource_files(self):
        return self.base_sprite.get_resource_files() + (THIS_FILE,)

    def get_data_layers(self, context):
        timer = context.start_timer()
        ret = LayeredImage.from_sprite(self.base_sprite)
        ret = make_foundation(ret, ZOOM_TO_SCALE[self.base_sprite.zoom], self.foundation_id)
        timer.count_composing()

        return ret.w, ret.h, ret.rgb, ret.alpha, ret.mask
