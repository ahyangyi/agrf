import numpy as np

from agrf.graphics.layered_image import LayeredImage
from agrf.graphics.cv.foundation import make_foundation_subimage, make_foundation


def _full_alpha_image(w=16, h=16, xofs=0, yofs=0):
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    alpha = np.full((h, w), 255, dtype=np.uint8)
    return LayeredImage(xofs, yofs, w, h, rgb, alpha, None)


def test_make_foundation_subimage_basic_left_side():
    base = _full_alpha_image()
    # part (6, 0) targets the left side (c <= 0) when scale=4 and xofs=0
    out = make_foundation_subimage(
        base, scale=4, left_parts=6, right_parts=None, s_shareground=True, cut_inside=False, zshift=0, solid=True
    )
    assert out.alpha is not None
    # Left-most column should be non-zero
    assert out.alpha[0, 0] > 0
    # A column clearly on the right should be zero
    assert out.alpha[0, 8] == 0


def test_make_foundation_subimage_alpha_none_passthrough():
    # If input has no alpha, output keeps alpha as None
    rgb = np.zeros((8, 8, 3), dtype=np.uint8)
    base = LayeredImage(0, 0, 8, 8, rgb, None, None)
    out = make_foundation_subimage(
        base, scale=4, left_parts=6, right_parts=None, s_shareground=True, cut_inside=False, zshift=0, solid=True
    )
    assert out.alpha is None


def test_make_foundation_passthrough_single_input():
    base = _full_alpha_image()
    # Only solid provided
    expected_solid = make_foundation_subimage(
        base.copy(), scale=4, left_parts=6, right_parts=None, s_shareground=True, cut_inside=False, zshift=0, solid=True
    )
    out_solid = make_foundation(
        base, None, scale=4, left_parts=6, right_parts=None, s_shareground=True, cut_inside=False, zshift=0
    )
    assert np.array_equal(out_solid.alpha, expected_solid.alpha)

    # Only ground provided
    expected_ground = make_foundation_subimage(
        base.copy(),
        scale=4,
        left_parts=6,
        right_parts=None,
        s_shareground=True,
        cut_inside=False,
        zshift=0,
        solid=False,
    )
    out_ground = make_foundation(
        None, base, scale=4, left_parts=6, right_parts=None, s_shareground=True, cut_inside=False, zshift=0
    )
    assert np.array_equal(out_ground.alpha, expected_ground.alpha)


def test_make_foundation_subimage_zshift_reduces_coverage_for_part0():
    # Use a large y offset to sit near the inequality boundary so zshift has an effect
    base = _full_alpha_image()
    base.yofs = 120
    out0 = make_foundation_subimage(
        base, scale=4, left_parts=6, right_parts=None, s_shareground=True, cut_inside=False, zshift=0, solid=True
    )
    out1 = make_foundation_subimage(
        base, scale=4, left_parts=6, right_parts=None, s_shareground=True, cut_inside=False, zshift=2, solid=True
    )
    sum0 = int(out0.alpha.sum())
    sum1 = int(out1.alpha.sum())
    assert sum0 > 0
    assert sum1 < sum0
