import grf
import numpy as np
from agrf.graphics import SCALE_TO_ZOOM

THIS_FILE = grf.PythonFile(__file__)


class EmptySprite(grf.Sprite):
    def __init__(self, w, h, xofs, yofs, zoom):
        self.w = w
        self.h = h
        self.xofs = xofs
        self.yofs = yofs
        self.zoom = zoom

    @property
    def bpp(self):
        return 8

    @property
    def crop(self):
        return False

    @property
    def default_name(self):
        return f"{self.w}x{self.h}"

    def prepare_files(self):
        pass

    def get_data_layers(self, context):
        mask = np.zeros((self.h, self.w), dtype=np.uint8)
        return self.w, self.h, None, None, mask

    def get_image_files(self):
        return None

    def get_fingerprint(self):
        return {"w": self.w, "h": self.h, "xofs": self.xofs, "yofs": self.yofs}

    def get_resource_files(self):
        return (THIS_FILE,)


def empty_alternatives(w, h, xofs, yofs):
    return grf.AlternativeSprites(*[EmptySprite(w * k, h * k, xofs * k, yofs * k, v) for k, v in SCALE_TO_ZOOM.items()])
