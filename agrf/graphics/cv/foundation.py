import grf
import numpy as np
from .. import LayeredImage


def make_foundation_subimage(
    img: LayeredImage, scale, left_parts, right_parts, cut_inside, zshift, solid
) -> LayeredImage:
    if img.alpha is not None:
        r = np.arange(img.h)[:, np.newaxis] + img.yofs + 0.5 + zshift * scale
        c = np.arange(img.w)[np.newaxis] + img.xofs - scale + 0.5

        alphamask = np.zeros((img.h, img.w), dtype=np.uint8)
        ones = np.ones((img.h, img.w), dtype=np.uint8)
        if left_parts is not None:
            left = ones * (c >= -32 * scale) * (c <= 0 * scale)

            # Top limit - not applicable to solid parts
            if not solid:
                if left_parts // 2 == 0:
                    left *= r * 2 + c >= 0 * scale
                elif left_parts // 2 == 1:
                    left *= r * 4 + c >= 0 * scale
                elif left_parts // 2 == 2:
                    left *= r * 4 + c * 3 >= -32 * scale
                else:
                    assert left_parts // 2 == 3
                    left *= r * 2 + c >= -16 * scale

            if left_parts % 4 == 0:
                left *= r * 2 - c <= 64 * scale
            elif left_parts % 4 == 1:
                left *= r * 4 - c <= 96 * scale
            elif left_parts % 4 == 2:
                left *= r * 4 - c * 3 <= 128 * scale
            else:
                assert left_parts % 4 == 3
                left *= r * 2 - c <= 48 * scale

            alphamask = np.maximum(alphamask, left)

        if right_parts is not None:
            right = ones * (c >= 0 * scale) * (c <= 32 * scale)

            # Top limit - not applicable to solid parts
            if not solid:
                if right_parts // 2 == 0:
                    right *= r * 2 - c >= 0 * scale
                elif right_parts // 2 == 1:
                    right *= r * 4 - c >= 0 * scale
                elif right_parts // 2 == 2:
                    right *= r * 4 - c * 3 >= -32 * scale
                else:
                    assert right_parts // 2 == 3
                    right *= r * 2 - c >= -16 * scale

            if right_parts % 4 == 0:
                right *= r * 2 + c <= 64 * scale
            elif right_parts % 4 == 1:
                right *= r * 4 + c <= 96 * scale
            elif right_parts % 4 == 2:
                right *= r * 4 + c * 3 <= 128 * scale
            else:
                assert right_parts % 4 == 3
                right *= r * 2 + c <= 48 * scale

            alphamask = np.maximum(alphamask, right)

        if cut_inside:
            # FIXME
            pass
        alpha = img.alpha * alphamask
    else:
        alpha = None

    return LayeredImage(xofs=img.xofs, yofs=img.yofs, w=img.w, h=img.h, rgb=img.rgb, alpha=alpha, mask=None)


def make_foundation(
    solid: LayeredImage, ground: LayeredImage, scale, left_parts, right_parts, cut_inside, zshift
) -> LayeredImage:
    if solid is not None:
        solid = make_foundation_subimage(solid, scale, left_parts, right_parts, cut_inside, zshift, True)
    if ground is not None:
        ground = make_foundation_subimage(ground, scale, left_parts, right_parts, cut_inside, zshift, False)
    if solid is not None and ground is not None:
        return ground.copy().blend_over(solid)
    return solid or ground
