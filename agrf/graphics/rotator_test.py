import numpy as np
import pytest

from .rotator import natural_dimens, unnatural_dimens

_TEST_SCALE = 2**0.5 / 13
_TEST_BBOX = {"x": 252, "y": 80, "z": 96}
_TEST_ANGLES = range(0, 91, 15)
NATURAL_DIMENS = [
    (8.70285269152674, 24.150416218986702),
    (15.501571850494896, 24.80959377046415),
    (21.243884505410545, 24.489740540816864),
    (25.538461538461537, 23.21265399906286),
    (28.09263462196956, 21.065365482537363),
    (28.732341081264128, 18.194209155079534),
    (27.413985978309228, 14.794849575595457),
]
UNNATURAL_DIMENS = [
    (8.70285269152674, 29.82803861444747),
    (16.599212651305336, 26.85781938900673),
    (21.727414862975703, 24.90849011396927),
    (25.538461538461537, 23.21265399906286),
    (28.930133768274363, 21.307130661319942),
    (32.82879231834929, 18.743029555484753),
    (38.76923076923077, 14.794849575595457),
]


@pytest.mark.parametrize("angle,expected", zip(_TEST_ANGLES, NATURAL_DIMENS))
def test_natural_dimens_matches_reference_values(angle, expected):
    np.testing.assert_allclose(
        natural_dimens(angle, _TEST_BBOX, _TEST_SCALE), expected, rtol=1e-6, atol=1e-6
    )


@pytest.mark.parametrize("angle,expected", zip(_TEST_ANGLES, UNNATURAL_DIMENS))
def test_unnatural_dimens_matches_reference_values(angle, expected):
    np.testing.assert_allclose(
        unnatural_dimens(angle, _TEST_BBOX, _TEST_SCALE), expected, rtol=1e-6, atol=1e-6
    )
