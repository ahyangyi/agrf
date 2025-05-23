import grf
import numpy as np
from .. import LayeredImage


def make_night_mask(img: LayeredImage, darkness=0.75) -> LayeredImage:
    if img.alpha is None:
        mask = ((img.mask > 0) * 255 * darkness).astype(np.uint8)
    else:
        a = img.alpha.astype(np.float32) / 255
        mask = ((1 - (1 - darkness) / ((1 - darkness) * (1 - a) + a)) * 255).astype(np.uint8)

    return LayeredImage(xofs=img.xofs, yofs=img.yofs, w=img.w, h=img.h, rgb=None, alpha=mask, mask=None)
