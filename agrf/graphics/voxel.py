import math
import os
import functools
from agrf.gorender import (
    Config,
    render,
    hill_positor_1,
    stairstep,
    compose,
    self_compose,
    produce_empty,
    discard_layers,
    keep_layers,
)
from agrf.graphics.rotator import unnatural_dimens
from agrf.graphics.spritesheet import spritesheet_template
from copy import deepcopy
from agrf.actions import FakeReferencingGenericSpriteLayout
from agrf.magic import CachedFunctorMixin


class LazyVoxel(Config):
    def __init__(self, name, *, prefix=None, voxel_getter=None, load_from=None, config=None, subset=None):
        super().__init__(load_from=load_from, config=config)
        if subset is not None:
            self.config["agrf_subset"] = subset
        self.name = name
        self.prefix = prefix
        self.voxel_getter = voxel_getter
        self._update_dimensions()

    def _update_dimensions(self):
        if "agrf_unnaturalness" not in self.config:
            return
        bounding_box = self.config["size"]
        for x in self.config["sprites"]:
            x["width"], x["height"] = map(
                math.ceil,
                unnatural_dimens(
                    x["angle"], bounding_box, self.config["agrf_scale"], unnaturalness=self.config["agrf_unnaturalness"]
                ),
            )

    def in_place_subset(self, subset):
        self.config["agrf_subset"] = subset

    @functools.cache
    def rotate(self, delta, suffix):
        new_config = deepcopy(self.config)
        for x in new_config["sprites"]:
            x["angle"] += delta
        return LazyVoxel(
            self.name, prefix=os.path.join(self.prefix, suffix), voxel_getter=self.voxel_getter, config=new_config
        )

    @functools.cache
    def change_pitch(self, delta, suffix):
        def voxel_getter():
            old_path = self.voxel_getter()
            new_path = os.path.join(self.prefix, suffix)
            hill_positor_1(old_path, new_path, delta)
            return os.path.join(new_path, f"{self.name}.vox")

        new_config = deepcopy(self.config)
        new_config["agrf_zdiff"] = new_config.get("agrf_zdiff", 0.0) + new_config.get(
            "agrf_real_x", new_config["size"]["x"]
        ) / 4 * math.sin(math.radians(abs(delta)))

        return LazyVoxel(
            self.name, prefix=os.path.join(self.prefix, suffix), voxel_getter=voxel_getter, config=new_config
        )

    @functools.cache
    def stairstep(self, x_steps, suffix):
        def voxel_getter():
            old_path = self.voxel_getter()
            new_path = os.path.join(self.prefix, suffix)
            stairstep(old_path, new_path, x_steps)
            return os.path.join(new_path, f"{self.name}.vox")

        new_config = deepcopy(self.config)
        real_x = new_config.get("agrf_real_x", new_config["size"]["x"])
        if new_config.get("agrf_road_mode"):
            real_x -= new_config["size"]["x"]
        new_config["agrf_zdiff"] = new_config.get("agrf_zdiff", 0.0) + real_x / 4 / abs(x_steps)

        return LazyVoxel(
            self.name, prefix=os.path.join(self.prefix, suffix), voxel_getter=voxel_getter, config=new_config
        )

    def update_config(self, new_config, suffix):
        return LazyVoxel(
            self.name,
            prefix=os.path.join(self.prefix, suffix),
            voxel_getter=self.voxel_getter,
            config={**deepcopy(self.config), **new_config},
        )

    @functools.cache
    def flip(self, suffix):
        new_config = deepcopy(self.config)
        for x in new_config["sprites"]:
            x["flip"] = not x.get("flip", False)
        return LazyVoxel(
            self.name, prefix=os.path.join(self.prefix, suffix), voxel_getter=self.voxel_getter, config=new_config
        )

    @functools.cache
    def compose(self, subvoxel, suffix, ignore_mask=False, colour_map=None):
        def voxel_getter(subvoxel=subvoxel):
            old_path = self.voxel_getter()
            new_path = os.path.join(self.prefix, suffix)
            if isinstance(subvoxel, str):
                subvoxel_path = subvoxel
            else:
                subvoxel_path = subvoxel.voxel_getter()
            if colour_map is not None:
                extra_config = colour_map.positor_config()
            else:
                extra_config = {}
            compose(old_path, subvoxel_path, new_path, {**extra_config, "ignore_mask": ignore_mask})
            return os.path.join(new_path, f"{self.name}.vox")

        return LazyVoxel(
            self.name, prefix=os.path.join(self.prefix, suffix), voxel_getter=voxel_getter, config=deepcopy(self.config)
        )

    @functools.cache
    def self_compose(self, suffix, colour_map=None):
        def voxel_getter():
            old_path = self.voxel_getter()
            new_path = os.path.join(self.prefix, suffix)
            if colour_map is not None:
                extra_config = colour_map.positor_config()
            else:
                extra_config = {}
            self_compose(old_path, new_path, extra_config)
            return os.path.join(new_path, f"{self.name}.vox")

        return LazyVoxel(
            self.name, prefix=os.path.join(self.prefix, suffix), voxel_getter=voxel_getter, config=deepcopy(self.config)
        )

    @functools.cache
    def produce_empty(self, suffix):
        def voxel_getter():
            old_path = self.voxel_getter()
            new_path = os.path.join(self.prefix, suffix)
            produce_empty(old_path, new_path)
            return os.path.join(new_path, f"{self.name}.vox")

        return LazyVoxel(
            self.name, prefix=os.path.join(self.prefix, suffix), voxel_getter=voxel_getter, config=deepcopy(self.config)
        )

    @functools.cache
    def mask_clip_away(self, subvoxel, suffix):
        def voxel_getter(subvoxel=subvoxel):
            old_path = self.voxel_getter()
            new_path = os.path.join(self.prefix, suffix)
            if isinstance(subvoxel, str):
                subvoxel_path = subvoxel
            else:
                subvoxel_path = subvoxel.voxel_getter()
            compose(
                old_path,
                subvoxel_path,
                new_path,
                {"ignore_mask": True, "overwrite": True, "n": 0, "truncate": True, "blend_mode": "atop"},
            )
            return os.path.join(new_path, f"{self.name}.vox")

        return LazyVoxel(
            self.name, prefix=os.path.join(self.prefix, suffix), voxel_getter=voxel_getter, config=deepcopy(self.config)
        )

    @functools.cache
    def discard_layers(self, discards, suffix):
        def voxel_getter():
            old_path = self.voxel_getter()
            new_path = os.path.join(self.prefix, suffix, f"{self.name}.vox")
            discard_layers(discards, old_path, new_path)
            return new_path

        return LazyVoxel(
            self.name, prefix=os.path.join(self.prefix, suffix), voxel_getter=voxel_getter, config=deepcopy(self.config)
        )

    @functools.cache
    def keep_layers(self, keeps, suffix):
        def voxel_getter():
            old_path = self.voxel_getter()
            new_path = os.path.join(self.prefix, suffix, f"{self.name}.vox")
            keep_layers(keeps, old_path, new_path)
            return new_path

        return LazyVoxel(
            self.name, prefix=os.path.join(self.prefix, suffix), voxel_getter=voxel_getter, config=deepcopy(self.config)
        )

    @functools.cache
    def squash(self, ratio, suffix):
        new_config = deepcopy(self.config)
        new_config["z_scale"] = new_config.get("z_scale", 1.0) * ratio
        new_config["agrf_scales"] = [x for x in new_config["agrf_scales"] if x < 4]
        if "agrf_manual_crop" in new_config:
            new_config["agrf_manual_crop"] = (
                new_config["agrf_manual_crop"][0],
                int(new_config["agrf_manual_crop"][1] * ratio),
            )
        if "agrf_childsprite" in new_config:
            new_config["agrf_childsprite"] = (
                new_config["agrf_childsprite"][0],
                int(new_config["agrf_childsprite"][1] * ratio),
            )
        return LazyVoxel(
            self.name, prefix=os.path.join(self.prefix, suffix), voxel_getter=self.voxel_getter, config=new_config
        )

    @functools.cache
    def render(self):
        voxel_path = self.voxel_getter()
        render(self, voxel_path, os.path.join(self.prefix, self.name))

    @functools.cache
    def spritesheet(self, xdiff=0, ydiff=0, zdiff=0, shift=0, xspan=16, yspan=16):
        real_xdiff = 0 if self.config.get("agrf_road_mode", False) else 0.5
        real_ydiff = (self.config.get("agrf_zdiff", 0) + zdiff) * self.config.get("agrf_scale", 1)

        return spritesheet_template(
            self,
            os.path.join(self.prefix, self.name),
            [(x["width"], x.get("height", 0)) for x in self.final_config["sprites"]],
            [x["angle"] for x in self.final_config["sprites"]],
            bbox=self.config["size"],
            deltas=self.final_config.get("agrf_deltas", None),
            ydeltas=self.final_config.get("agrf_ydeltas", None),
            offsets=self.final_config.get("agrf_offsets", None),
            yoffsets=self.final_config.get("agrf_yoffsets", None),
            z_scale=self.config.get("z_scale", 1.0),
            bbox_joggle=self.config.get("agrf_bbox_joggle", None),
            xdiff=real_xdiff,
            ydiff=real_ydiff,
            road_mode=self.config.get("agrf_road_mode", False),
            bpps=self.config["agrf_bpps"],
            scales=self.config["agrf_scales"],
            shift=shift,
            manual_crop=self.config.get("agrf_manual_crop", None),
            childsprite=self.config.get("agrf_childsprite", False),
            relative_childsprite=self.config.get("agrf_relative_childsprite", False),
            kwargs={"xdiff": xdiff, "ydiff": ydiff, "zdiff": zdiff, "shift": shift, "xspan": xspan, "yspan": yspan},
        )

    @functools.cache
    def get_action(self, feature, xdiff=0, zdiff=0, shift=0):
        return FakeReferencingGenericSpriteLayout(feature, (self.spritesheet(xdiff=xdiff, zdiff=zdiff, shift=shift),))

    def get_default_graphics(self):
        return self


class LazySpriteSheet(CachedFunctorMixin):
    def __init__(self, sprites, indices):
        super().__init__()
        self.sprites = sprites
        self.indices = indices

    def fmap(self, f):
        return LazySpriteSheet(tuple(f(x) for x in self.sprites), self.indices)

    @functools.cache
    def spritesheet(self, xdiff=0, zdiff=0, shift=0):
        spritesheets = [x.spritesheet(xdiff, shift) for x in self.sprites]
        return [spritesheets[i][j] for (i, j) in self.indices]

    @functools.cache
    def get_action(self, xdiff, shift, feature):
        return FakeReferencingGenericSpriteLayout(feature, (self.spritesheet(xdiff=xdiff, shift=shift),))

    def get_default_graphics(self):
        return self


class LazyAlternatives(CachedFunctorMixin):
    def __init__(self, sprites, loading_sprites=None):
        super().__init__()
        self.sprites = sprites
        self.loading_sprites = loading_sprites

    def fmap(self, f):
        return LazyAlternatives(
            tuple(f(x) for x in self.sprites), self.loading_sprites and tuple(f(x) for x in self.loading_sprites)
        )

    @functools.cache
    def get_action(self, feature, xdiff=0, zdiff=0, shift=0):
        return FakeReferencingGenericSpriteLayout(
            feature,
            tuple(x.spritesheet(xdiff=xdiff, shift=shift) for x in self.sprites),
            None if self.loading_sprites is None else tuple(x.spritesheet(xdiff, shift) for x in self.loading_sprites),
        )

    def get_default_graphics(self):
        return self.sprites[-1]
