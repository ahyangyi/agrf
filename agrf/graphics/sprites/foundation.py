import grf
from agrf.graphics.cv.foundation import make_foundation, THIS_FILE as CV_FILE
from agrf.graphics import LayeredImage, SCALE_TO_ZOOM, ZOOM_TO_SCALE
from agrf.graphics.spritesheet import LazyAlternativeSprites


THIS_FILE = grf.PythonFile(__file__)


class FoundationSprite(grf.Sprite):
    def __init__(self, solid_sprite, ground_sprite, left_parts, right_parts, y_limit, cut_inside, zshift, zoffset):
        representative = ground_sprite or solid_sprite
        super().__init__(
            representative.w,
            representative.h,
            zoom=representative.zoom,
            xofs=0,
            yofs=0,
            bpp=representative.bpp,
            crop=representative.crop,
        )
        self.solid_sprite = solid_sprite
        self.ground_sprite = ground_sprite
        self.left_parts = left_parts
        self.right_parts = right_parts
        self.y_limit = y_limit
        self.cut_inside = cut_inside
        self.zshift = zshift
        self.zoffset = zoffset

    def get_fingerprint(self):
        return {
            "solid_sprite": self.solid_sprite.get_fingerprint() if self.solid_sprite is not None else None,
            "ground_sprite": self.ground_sprite.get_fingerprint() if self.ground_sprite is not None else None,
            "left_parts": self.left_parts,
            "right_parts": self.right_parts,
            "y_limit": self.y_limit,
            "cut_inside": self.cut_inside,
            "zshift": self.zshift,
            "zoffset": self.zoffset,
        }

    def get_resource_files(self):
        return (
            (self.solid_sprite.get_resource_files() if self.solid_sprite is not None else ())
            + (self.ground_sprite.get_resource_files() if self.ground_sprite is not None else ())
            + (THIS_FILE, CV_FILE)
        )

    def get_data_layers(self, context):
        timer = context.start_timer()
        solid = self.solid_sprite and LayeredImage.from_sprite(self.solid_sprite)
        ground = self.ground_sprite and LayeredImage.from_sprite(self.ground_sprite)
        ret = make_foundation(
            solid,
            ground,
            ZOOM_TO_SCALE[(self.solid_sprite or self.ground_sprite).zoom],
            self.left_parts,
            self.right_parts,
            self.y_limit,
            self.cut_inside,
            self.zshift,
        )
        timer.count_composing()

        self.xofs = ret.xofs
        self.yofs = ret.yofs + (self.zoffset + self.zshift) * ZOOM_TO_SCALE[self.zoom]

        return ret.w, ret.h, ret.rgb, ret.alpha, ret.mask
