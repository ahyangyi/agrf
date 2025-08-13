import pytest
import numpy as np
from .layered_image import LayeredImage


def test_blend_over_basic_rgb_alpha():
    """Test basic RGB + alpha blending with concrete arrays"""
    base = LayeredImage(
        xofs=0,
        yofs=0,
        w=2,
        h=2,
        rgb=np.array([[[255, 255, 255], [255, 255, 255]], [[255, 255, 255], [255, 255, 255]]], dtype=np.uint8),
        alpha=np.array([[128, 128], [128, 128]], dtype=np.uint8),
        mask=None,
    )

    overlay = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[255, 0, 0]]], dtype=np.uint8),
        alpha=np.array([[255]], dtype=np.uint8),
        mask=None,
    )

    result = base.blend_over(overlay)

    expected_rgb = np.array([[[255, 0, 0], [255, 255, 255]], [[255, 255, 255], [255, 255, 255]]], dtype=np.uint8)
    expected_alpha = np.array([[255, 128], [128, 128]], dtype=np.uint8)

    np.testing.assert_array_equal(result.rgb, expected_rgb)
    np.testing.assert_array_equal(result.alpha, expected_alpha)


def test_blend_over_transparent_overlay():
    """Test blending with transparent overlay (alpha=0)"""
    base = LayeredImage(
        xofs=0,
        yofs=0,
        w=2,
        h=2,
        rgb=np.array([[[0, 0, 255], [0, 0, 255]], [[0, 0, 255], [0, 0, 255]]], dtype=np.uint8),
        alpha=np.array([[255, 255], [255, 255]], dtype=np.uint8),
        mask=None,
    )

    overlay = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[255, 0, 0]]], dtype=np.uint8),
        alpha=np.array([[0]], dtype=np.uint8),
        mask=None,
    )

    result = base.blend_over(overlay)

    expected_rgb = np.array([[[0, 0, 255], [0, 0, 255]], [[0, 0, 255], [0, 0, 255]]], dtype=np.uint8)
    expected_alpha = np.array([[255, 255], [255, 255]], dtype=np.uint8)

    np.testing.assert_array_equal(result.rgb, expected_rgb)
    np.testing.assert_array_equal(result.alpha, expected_alpha)


def test_blend_over_partial_alpha():
    """Test blending with partial alpha values"""
    base = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[255, 255, 255]]], dtype=np.uint8),
        alpha=np.array([[255]], dtype=np.uint8),
        mask=None,
    )

    overlay = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[0, 0, 0]]], dtype=np.uint8),
        alpha=np.array([[128]], dtype=np.uint8),
        mask=None,
    )

    result = base.blend_over(overlay)

    assert result.rgb[0, 0, 0] < 255
    assert result.rgb[0, 0, 0] > 0
    assert result.alpha[0, 0] == 255


def test_blend_over_with_mask():
    """Test blending with mask layers (palette image where 0=transparent)"""
    base = LayeredImage(
        xofs=0,
        yofs=0,
        w=2,
        h=2,
        rgb=None,
        alpha=None,
        mask=np.array([[5, 5], [5, 5]], dtype=np.uint8),  # Palette index 5
    )

    overlay = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=None,
        alpha=None,
        mask=np.array([[0]], dtype=np.uint8),  # Transparent (palette index 0)
    )

    result = base.blend_over(overlay)

    expected_mask = np.array([[5, 5], [5, 5]], dtype=np.uint8)
    np.testing.assert_array_equal(result.mask, expected_mask)


def test_blend_over_with_mask_non_zero():
    """Test blending with non-zero mask values (palette indices)"""
    base = LayeredImage(
        xofs=0,
        yofs=0,
        w=2,
        h=2,
        rgb=None,
        alpha=None,
        mask=np.array([[5, 5], [5, 5]], dtype=np.uint8),  # Palette index 5
    )

    overlay = LayeredImage(
        xofs=0, yofs=0, w=1, h=1, rgb=None, alpha=None, mask=np.array([[10]], dtype=np.uint8)  # Palette index 10
    )

    result = base.blend_over(overlay)

    expected_mask = np.array([[10, 5], [5, 5]], dtype=np.uint8)
    np.testing.assert_array_equal(result.mask, expected_mask)


def test_blend_over_rgb_with_mask():
    """Test blending RGB image with mask (mask index 0 should not overwrite RGB)"""
    base = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[255, 255, 255]]], dtype=np.uint8),
        alpha=np.array([[255]], dtype=np.uint8),
        mask=None,
    )

    overlay = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=None,
        alpha=None,
        mask=np.array([[0]], dtype=np.uint8),  # Transparent (palette index 0)
    )

    result = base.blend_over(overlay)

    expected_rgb = np.array([[[255, 255, 255]]], dtype=np.uint8)
    expected_alpha = np.array([[255]], dtype=np.uint8)

    np.testing.assert_array_equal(result.rgb, expected_rgb)
    np.testing.assert_array_equal(result.alpha, expected_alpha)


def test_blend_over_rgb_with_non_zero_mask():
    """Test blending RGB image with non-zero mask (should affect alpha calculation)"""
    base = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[255, 255, 255]]], dtype=np.uint8),
        alpha=np.array([[255]], dtype=np.uint8),
        mask=None,
    )

    overlay = LayeredImage(
        xofs=0, yofs=0, w=1, h=1, rgb=None, alpha=None, mask=np.array([[10]], dtype=np.uint8)  # Non-zero palette index
    )

    result = base.blend_over(overlay)

    expected_rgb = np.array([[[255, 255, 255]]], dtype=np.uint8)
    expected_alpha = np.array([[255]], dtype=np.uint8)

    np.testing.assert_array_equal(result.rgb, expected_rgb)
    np.testing.assert_array_equal(result.alpha, expected_alpha)


def test_blend_over_empty_overlay():
    """Test blending with empty overlay (no rgb, alpha, or mask)"""
    base = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[255, 255, 255]]], dtype=np.uint8),
        alpha=np.array([[255]], dtype=np.uint8),
        mask=None,
    )

    overlay = LayeredImage(xofs=0, yofs=0, w=1, h=1, rgb=None, alpha=None, mask=None)

    result = base.blend_over(overlay)

    expected_rgb = np.array([[[255, 255, 255]]], dtype=np.uint8)
    expected_alpha = np.array([[255]], dtype=np.uint8)

    np.testing.assert_array_equal(result.rgb, expected_rgb)
    np.testing.assert_array_equal(result.alpha, expected_alpha)


def test_blend_over_empty_base():
    """Test blending when base is empty and overlay has content"""
    base = LayeredImage(xofs=0, yofs=0, w=1, h=1, rgb=None, alpha=None, mask=None)

    overlay = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[0, 255, 0]]], dtype=np.uint8),
        alpha=np.array([[255]], dtype=np.uint8),
        mask=None,
    )

    result = base.blend_over(overlay)

    expected_rgb = np.array([[[0, 255, 0]]], dtype=np.uint8)
    expected_alpha = np.array([[255]], dtype=np.uint8)

    np.testing.assert_array_equal(result.rgb, expected_rgb)
    np.testing.assert_array_equal(result.alpha, expected_alpha)


def test_blend_over_with_offset():
    """Test blending with offset positioning"""
    base = LayeredImage(
        xofs=0,
        yofs=0,
        w=3,
        h=3,
        rgb=np.array(
            [
                [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
                [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
                [[255, 255, 255], [255, 255, 255], [255, 255, 255]],
            ],
            dtype=np.uint8,
        ),
        alpha=np.array([[255, 255, 255], [255, 255, 255], [255, 255, 255]], dtype=np.uint8),
        mask=None,
    )

    overlay = LayeredImage(
        xofs=1,
        yofs=1,
        w=1,
        h=1,
        rgb=np.array([[[255, 0, 0]]], dtype=np.uint8),
        alpha=np.array([[255]], dtype=np.uint8),
        mask=None,
    )

    result = base.blend_over(overlay)

    assert result.rgb[1, 1, 0] == 255
    assert result.rgb[1, 1, 1] == 0
    assert result.rgb[1, 1, 2] == 0

    assert result.rgb[0, 0, 0] == 255
    assert result.rgb[2, 2, 0] == 255


def test_blend_over_semitransparent_overlay():
    """Test blending with a semitransparent overlay"""
    base = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[255, 255, 255]]], dtype=np.uint8),
        alpha=np.array([[255]], dtype=np.uint8),
        mask=None,
    )

    overlay = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[255, 0, 0]]], dtype=np.uint8),
        alpha=np.array([[128]], dtype=np.uint8),  # 50% alpha
        mask=None,
    )

    result = base.blend_over(overlay)

    assert result.rgb[0, 0, 0] == 255
    assert result.rgb[0, 0, 1] < 255
    assert result.rgb[0, 0, 1] > 0
    assert result.rgb[0, 0, 2] < 255
    assert result.rgb[0, 0, 2] > 0
    assert result.alpha[0, 0] == 255


def test_blend_over_custom_alpha_parameter():
    """Test blending with custom alpha parameter (not 255)"""
    base = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[255, 255, 255]]], dtype=np.uint8),
        alpha=np.array([[255]], dtype=np.uint8),
        mask=None,
    )

    overlay = LayeredImage(
        xofs=0,
        yofs=0,
        w=1,
        h=1,
        rgb=np.array([[[0, 0, 0]]], dtype=np.uint8),
        alpha=np.array([[255]], dtype=np.uint8),
        mask=None,
    )

    result = base.blend_over(overlay, alpha=128)

    assert result.rgb[0, 0, 0] > 0
    assert result.rgb[0, 0, 0] < 255
