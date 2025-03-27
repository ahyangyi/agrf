import grf
from agrf.graphics.cv.foundation import make_foundation
from agrf.graphics import LayeredImage, SCALE_TO_ZOOM, ZOOM_TO_SCALE
from agrf.graphics.spritesheet import LazyAlternativeSprites


THIS_FILE = grf.PythonFile(__file__)


class FoundationSprite(grf.Sprite):
    def __init__(self, solid_sprite, ground_sprite, foundation_id, cut_inside, zshift):
        representative = ground_sprite or solid_sprite
        super().__init__(
            representative.w,
            representative.h,
            zoom=representative.zoom,
            xofs=representative.xofs,
            yofs=representative.yofs
            + (8 * ZOOM_TO_SCALE[representative.zoom] if foundation_id == 8 else 0)
            + zshift * ZOOM_TO_SCALE[representative.zoom],
            bpp=representative.bpp,
            crop=representative.crop,
        )
        self.solid_sprite = solid_sprite
        self.ground_sprite = ground_sprite
        self.foundation_id = foundation_id
        self.cut_inside = cut_inside
        self.zshift = zshift

    def get_fingerprint(self):
        return {
            "solid_sprite": self.solid_sprite.get_fingerprint() if self.solid_sprite is not None else None,
            "ground_sprite": self.ground_sprite.get_fingerprint() if self.ground_sprite is not None else None,
            "foundation_id": self.foundation_id,
            "cut_inside": self.cut_inside,
            "zshift": self.zshift,
        }

    def get_resource_files(self):
        return (
            (self.solid_sprite.get_resource_files() if self.solid_sprite is not None else ())
            + (self.ground_sprite.get_resource_files() if self.ground_sprite is not None else ())
            + (THIS_FILE,)
        )

    def get_data_layers(self, context):
        timer = context.start_timer()
        solid = self.solid_sprite and LayeredImage.from_sprite(self.solid_sprite)
        ground = self.ground_sprite and LayeredImage.from_sprite(self.ground_sprite)
        ret = make_foundation(
            solid,
            ground,
            ZOOM_TO_SCALE[(self.solid_sprite or self.ground_sprite).zoom],
            self.foundation_id,
            self.cut_inside,
        )
        timer.count_composing()

        return ret.w, ret.h, ret.rgb, ret.alpha, ret.mask
