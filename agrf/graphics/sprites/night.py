import grf
from agrf.graphics.cv.nightmask import make_night_mask
from agrf.graphics import LayeredImage, SCALE_TO_ZOOM, ZOOM_TO_SCALE
from agrf.graphics.spritesheet import LazyAlternativeSprites


THIS_FILE = grf.PythonFile(__file__)


class NightSprite(grf.Sprite):
    def __init__(
        self, base_sprite, scale, base_bpp, xofs=0, yofs=0, darkness=0.75, automatic_offset_mode=None, **kwargs
    ):
        s = base_sprite.get_sprite(zoom=SCALE_TO_ZOOM[scale], bpp=base_bpp)
        if automatic_offset_mode == "parent":
            if isinstance(base_sprite, LazyAlternativeSprites) and "agrf_manual_crop" in base_sprite.voxel.config:
                dx, dy = base_sprite.voxel.config["agrf_manual_crop"]
                xofs -= dx * scale
                yofs -= dy * scale
            else:
                assert not base_sprite.get_sprite(zoom=SCALE_TO_ZOOM[scale], bpp=base_bpp).crop
        elif automatic_offset_mode == "child":
            xofs += s.xofs
            yofs += s.yofs

        super().__init__(s.w, s.h, zoom=SCALE_TO_ZOOM[scale], xofs=xofs, yofs=yofs, bpp=8, crop=True, **kwargs)
        assert base_sprite is not None and "get_fingerprint" in dir(base_sprite), f"base_sprite {type(base_sprite)}"
        self.base_sprite = base_sprite
        self.scale = scale
        self.base_bpp = base_bpp
        self.darkness = darkness

    def get_fingerprint(self):
        return {
            "base_sprite": self.base_sprite.get_fingerprint(),
            "w": self.w,
            "h": self.h,
            "bpp": self.bpp,
            "base_bpp": self.base_bpp,
            "scale": self.scale,
            "xofs": self.xofs,
            "yofs": self.yofs,
            "darkness": self.darkness,
        }

    def get_resource_files(self):
        return self.base_sprite.get_resource_files() + [THIS_FILE]

    def get_data_layers(self, context):
        timer = context.start_timer()
        sprite = self.base_sprite.get_sprite(zoom=SCALE_TO_ZOOM[self.scale], bpp=self.base_bpp)
        assert sprite is not None

        ret = LayeredImage.from_sprite(sprite)
        ret = make_night_mask(ret, darkness=self.darkness)
        timer.count_composing()

        return ret.w, ret.h, ret.rgb, ret.alpha, ret.mask
