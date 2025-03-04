import grf
import numpy as np
from .. import LayeredImage


def make_foundation(img: LayeredImage, scale, part) -> LayeredImage:
    if img.alpha is not None:
        r = np.arange(img.shape[0])[:, np.newaxis] + img.yofs
        c = np.arange(img.shape[1])[np.newaxis] + img.xofs
        if part == 0:
            alphamask = r * 3 + c * 4 >= -160 * scale
        else:
            alphamask = 1
        alpha = img.alpha * alphamask
    else:
        alpha = None

    return LayeredImage(xofs=img.xofs, yofs=img.yofs, w=img.w, h=img.h, rgb=rgb, alpha=alpha, mask=None)
