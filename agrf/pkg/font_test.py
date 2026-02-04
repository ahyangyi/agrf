import numpy as np
from PIL import Image, ImageDraw

from . import load_font


def test_font():
    font = load_font("resources/fonts/AntaeusConsoleNumbers.otf", 12)
    img = Image.new("L", (64, 32), 0)
    draw = ImageDraw.Draw(img)
    # Expected values measured from rendering "42" using the bundled digits-only font at size 12.
    expected_text_width_for_42 = 12
    expected_non_zero_pixels_for_42 = 52
    _, _, width, _ = draw.textbbox((0, 0), "42", font=font)
    assert width == expected_text_width_for_42
    draw.text((0, 0), "42", 255, font=font)
    non_zero_pixels = np.count_nonzero(np.asarray(img))
    assert non_zero_pixels == expected_non_zero_pixels_for_42
