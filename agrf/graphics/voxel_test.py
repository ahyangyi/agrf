import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import math
from agrf.graphics.voxel import LazyVoxel, LazySpriteSheet, LazyAlternatives


class TestLazyVoxel:
    def test_lazy_voxel_updates_dimensions_with_unnaturalness(self):
        """Test that _update_dimensions actually updates sprite dimensions."""
        voxel_getter = Mock(return_value="/path/to/test.vox")
        config = {
            "sprites": [{"width": 32, "height": 32, "angle": 45}, {"width": 48, "height": 48, "angle": 90}],
            "size": {"x": 10, "y": 10, "z": 20},
            "agrf_unnaturalness": 1.5,
            "agrf_scale": 1.0,
        }

        with patch("agrf.graphics.voxel.unnatural_dimens") as mock_unnatural:
            mock_unnatural.return_value = (35.5, 35.5)

            voxel = LazyVoxel(name="test_voxel", config=config)

            # Verify that unnatural_dimens was called for each sprite
            assert mock_unnatural.call_count == 2

            # Verify dimensions were updated
            for sprite in voxel.config["sprites"]:
                assert sprite["width"] == 36  # math.ceil(35.5)
                assert sprite["height"] == 36

    def test_lazy_voxel_rotate(self):
        """Test rotate method creates rotated voxel instance."""
        voxel_getter = Mock(return_value="/path/to/test.vox")
        config = {"sprites": [{"width": 32, "height": 32, "angle": 45}], "size": {"x": 10, "y": 10, "z": 20}}

        voxel = LazyVoxel(name="test_voxel", prefix="/base", voxel_getter=voxel_getter, config=config)

        # Rotate by 90 degrees with suffix
        rotated = voxel.rotate(90, "rotated")

        # Verify new instance is created with updated angle
        assert rotated is not voxel  # Must be different instance
        assert rotated.name == "test_voxel"
        assert rotated.prefix == os.path.join("/base", "rotated")
        assert rotated.voxel_getter == voxel_getter
        assert rotated.config["sprites"][0]["angle"] == 135  # 45 + 90
        assert isinstance(rotated, LazyVoxel)

    def test_lazy_voxel_flip(self):
        """Test flip method creates flipped voxel instance."""
        voxel_getter = Mock(return_value="/path/to/test.vox")
        config = {
            "sprites": [{"width": 32, "height": 32, "angle": 45, "flip": False}],
            "size": {"x": 10, "y": 10, "z": 20},
        }

        voxel = LazyVoxel(name="test_voxel", prefix="/base", voxel_getter=voxel_getter, config=config)

        # Flip the voxel with suffix
        flipped = voxel.flip("flipped")

        # Verify new instance is created with flipped flag
        assert flipped is not voxel  # Must be different instance
        assert flipped.name == "test_voxel"
        assert flipped.prefix == os.path.join("/base", "flipped")
        assert flipped.voxel_getter == voxel_getter
        assert flipped.config["sprites"][0]["flip"] is True
        assert isinstance(flipped, LazyVoxel)

        # Test flipping a sprite that already has flip=True
        config_with_flip = {
            "sprites": [{"width": 32, "height": 32, "angle": 45, "flip": True}],
            "size": {"x": 10, "y": 10, "z": 20},
        }
        voxel_with_flip = LazyVoxel(
            name="test_voxel", prefix="/base", voxel_getter=voxel_getter, config=config_with_flip
        )

        flipped_twice = voxel_with_flip.flip("flipped_twice")
        assert flipped_twice.config["sprites"][0]["flip"] is False
