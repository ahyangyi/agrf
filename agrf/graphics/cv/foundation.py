import grf
import numpy as np
from .. import LayeredImage


def make_foundation_subimage(img: LayeredImage, scale, part, cut_inside, zshift, solid) -> LayeredImage:
    if img.alpha is not None:
        r = np.arange(img.h)[:, np.newaxis] + img.yofs + 0.5 + zshift * scale
        c = np.arange(img.w)[np.newaxis] + img.xofs - scale + 0.5
        if part == 0:
            alphamask = (r * 4 - c * 3 <= 128 * scale) * (c <= 0)
            if cut_inside:
                alphamask *= r * 2 - c >= 48 * scale
            elif not solid:
                alphamask *= r * 2 + c >= -16 * scale
        elif part == 1:
            alphamask = (r * 2 - c <= 64 * scale) * (c <= 0)
            if cut_inside:
                alphamask *= r * 2 - c >= 48 * scale
            elif not solid:
                alphamask *= r * 4 + c * 3 >= -32 * scale
        elif part == 2:
            alphamask = (r * 4 - c * 1 <= 96 * scale) * (c <= 0)
            if cut_inside:
                alphamask *= r * 2 - c >= 48 * scale
            elif not solid:
                alphamask *= r * 2 + c >= 0
        elif part == 3:
            alphamask = (r * 4 + c * 3 <= 128 * scale) * (c >= 0)
            if cut_inside:
                alphamask *= r * 2 + c >= 48 * scale
            elif not solid:
                alphamask *= r * 2 - c >= -16 * scale
        elif part == 4:
            alphamask = (r * 2 + c <= 64 * scale) * (c >= 0)
            if cut_inside:
                alphamask *= r * 2 + c >= 48 * scale
            elif not solid:
                alphamask *= r * 4 - c * 3 >= -32 * scale
        elif part == 5:
            alphamask = (r * 4 + c * 1 <= 96 * scale) * (c >= 0)
            if cut_inside:
                alphamask *= r * 2 + c >= 48 * scale
            elif not solid:
                alphamask *= r * 2 - c >= 0
        elif part == 6:
            if cut_inside:
                alphamask = (r * 2 + c <= -16 * scale) * (c <= 0)
            else:
                alphamask = 0
        elif part == 7:
            if cut_inside:
                alphamask = (r * 2 - c <= -16 * scale) * (c >= 0)
            else:
                alphamask = 0
        elif part == 8:
            if cut_inside:
                raise NotImplementedError()
            else:
                alphamask = (
                    (r * 2 - c <= 48 * scale)
                    * (r * 2 + c <= 48 * scale)
                    * (r * 2 + c >= -16 * scale)
                    * (r * 2 - c >= -16 * scale)
                )
        else:
            assert false, f"Unsupported part: {part}"
        alpha = img.alpha * alphamask
    else:
        alpha = None

    return LayeredImage(xofs=img.xofs, yofs=img.yofs, w=img.w, h=img.h, rgb=img.rgb, alpha=alpha, mask=None)


def make_foundation(solid: LayeredImage, ground: LayeredImage, scale, part, cut_inside, zshift) -> LayeredImage:
    if solid is not None:
        solid = make_foundation_subimage(solid, scale, part, cut_inside, zshift, True)
    if ground is not None:
        ground = make_foundation_subimage(ground, scale, part, cut_inside, zshift, False)
    if solid is not None and ground is not None:
        return ground.copy().blend_over(solid)
    return solid or ground
