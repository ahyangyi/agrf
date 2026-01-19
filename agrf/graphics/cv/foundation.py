import grf
import numpy as np
from .. import LayeredImage

THIS_FILE = grf.PythonFile(__file__)


def get_left_part(left_parts, r, c, solid):
    left = np.ones_like(r, dtype=np.uint8) * ((c >= -32) * (c <= 0))

    # Top limit - not applicable to solid parts
    # special case for None which indicates a quarter-base in simple mode
    if left_parts[2] is None:
        left *= r >= 8
    else:
        if not solid:
            if left_parts[2] == left_parts[3]:
                left *= r * 2 + c >= (-16 * left_parts[3])
            elif left_parts[2] == left_parts[3] + 1:
                left *= r * 4 + c >= (-16 * left_parts[3]) * 2
            else:
                assert left_parts[2] == left_parts[3] - 1
                left *= r * 4 + c * 3 >= (-16 * left_parts[3]) * 2

    if left_parts[0] is None:
        left *= r <= 8
    elif left_parts[0] == left_parts[1]:
        left *= r * 2 - c <= (64 - 16 * left_parts[0])
    elif left_parts[0] == left_parts[1] + 1:
        left *= r * 4 - c <= (64 - 16 * left_parts[0]) * 2
    else:
        assert left_parts[0] == left_parts[1] - 1
        left *= r * 4 - c * 3 <= (64 - 16 * left_parts[0]) * 2

    return left.astype(np.uint8)


def make_foundation_subimage(
    img: LayeredImage, scale, left_parts, right_parts, nw, ne, sw, se, y_limit, cut_inside, zshift, solid
) -> LayeredImage:
    r = (np.arange(img.h)[:, np.newaxis] + img.yofs + 1.0) / scale + zshift
    c = (np.arange(img.w)[np.newaxis] + img.xofs + 0.5) / scale - 1

    alphamask = np.zeros((img.h, img.w), dtype=np.uint8)
    if left_parts is not None:
        alphamask = np.maximum(alphamask, get_left_part(left_parts, r, c, solid))

    if right_parts is not None:
        alphamask = np.maximum(alphamask, get_left_part(right_parts, r, -c, solid))

    if cut_inside:
        alphamask *= (1 - (r * 2 + c >= -16) * (r * 2 - c >= -16) * (r * 2 + c < 48) * (r * 2 - c < 48)).astype(
            np.uint8
        )

    if not solid:
        if nw:
            alphamask *= (1 - (c < 0) * (r * 2 + c < 0) * (r * 2 - c < 48)).astype(np.uint8)
        if ne:
            alphamask *= (1 - (c > 0) * (r * 2 - c < 0) * (r * 2 + c < 48)).astype(np.uint8)

    if sw:
        sw_mask = r * 4 - c > y_limit * 2
    else:
        sw_mask = r * 2 - c > y_limit
    if se:
        se_mask = r * 4 + c > y_limit * 2
    else:
        se_mask = r * 2 + c > y_limit
    alphamask *= (1 - sw_mask * se_mask).astype(np.uint8)

    if img.alpha is None:
        alpha = None
        assert img.mask is not None
        assert img.rgb is None
        mask = img.mask * alphamask
    else:
        alpha = img.alpha * alphamask
        assert img.rgb is not None
        mask = img.mask

    return LayeredImage(xofs=img.xofs, yofs=img.yofs, w=img.w, h=img.h, rgb=img.rgb, alpha=alpha, mask=mask)


def make_foundation(
    solid: LayeredImage,
    ground: LayeredImage,
    scale,
    left_parts,
    right_parts,
    nw,
    ne,
    sw,
    se,
    y_limit,
    cut_inside,
    zshift,
) -> LayeredImage:
    if solid is not None:
        solid = make_foundation_subimage(
            solid, scale, left_parts, right_parts, nw, ne, sw, se, y_limit, cut_inside, zshift, True
        )
    if ground is not None:
        ground = make_foundation_subimage(
            ground, scale, left_parts, right_parts, nw, ne, sw, se, y_limit, cut_inside, zshift, False
        )
    if solid is not None and ground is not None:
        return ground.copy().blend_over(solid)
    return solid or ground
