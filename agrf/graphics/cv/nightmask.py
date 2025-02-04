import grf
import numpy as np
from .. import LayeredImage

THIS_FILE = grf.PythonFile(__file__)


def make_night_mask(img: LayeredImage, darkness=0.75) -> LayeredImage:
    if img.alpha is None:
        mask = ((img.mask > 0) * 255 * darkness).astype(np.uint8)
    else:
        mask = (img.alpha * darkness).astype(np.uint8)

    return LayeredImage(
        xofs=img.xofs,
        yofs=img.yofs,
        w=img.w,
        h=img.h,
        rgb=None,
        alpha=mask,
        mask=np.zeros((img.h, img.w), dtype=np.uint8),
    )
