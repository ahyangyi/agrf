import grf
import numpy as np
from .. import LayeredImage


def make_foundation(img: LayeredImage, scale, part) -> LayeredImage:
    if img.alpha is not None:
        r = np.arange(img.h)[:, np.newaxis] + img.yofs
        c = np.arange(img.w)[np.newaxis] + img.xofs
        if part == 0:
            alphamask = (r * 4 - c * 3 <= 128 * scale) * (c <= 0) * (r * 2 - c >= 48 * scale)
        elif part == 1:
            alphamask = (r * 2 - c <= 64 * scale) * (c <= 0) * (r * 2 - c >= 48 * scale)
        elif part == 2:
            alphamask = (r * 2 - c <= 64 * scale) * (c <= 0) * (r * 4 - c * 3 >= 128 * scale)
        elif part == 3:
            alphamask = (r * 4 + c * 3 <= 128 * scale) * (c >= 0) * (r * 2 + c >= 48 * scale)
        elif part == 4:
            alphamask = (r * 2 + c <= 64 * scale) * (c >= 0) * (r * 2 + c >= 48 * scale)
        elif part == 5:
            alphamask = (r * 2 + c <= 64 * scale) * (c >= 0) * (r * 4 + c * 3 >= 128 * scale)
        elif part == 6:
            alphamask = (r * 2 + c >= -64 * scale) * (c <= 0)
        elif part == 7:
            alphamask = (r * 2 - c >= -64 * scale) * (c >= 0)
        else:
            assert false, f"Unsupported part: {part}"
        alpha = img.alpha * alphamask
    else:
        alpha = None

    return LayeredImage(xofs=img.xofs, yofs=img.yofs, w=img.w, h=img.h, rgb=img.rgb, alpha=alpha, mask=None)
