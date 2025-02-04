import os
import numpy as np
import grf
import math
import functools
from .misc import SCALE_TO_ZOOM, ZOOM_TO_SCALE

THIS_FILE = grf.PythonFile(__file__)


__image_file_cache = {}


def make_image_file(path):
    if path in __image_file_cache:
        return __image_file_cache[path]
    __image_file_cache[path] = grf.ImageFile(path)
    return __image_file_cache[path]


def guess_dimens(width, height, angle, bbox, z_scale):
    radian = math.radians(angle)
    cos, sin = math.cos(radian), math.sin(radian)

    x, y, z = bbox["x"], bbox["y"], bbox["z"] * z_scale

    xcom, ycom = abs(x * cos), abs(y * sin)
    pxcom, pycom = abs(x * sin), abs(y * cos)

    horizontal_height = (xcom + ycom) * 0.5

    if height == 0:
        ratio = (horizontal_height + z) / (pxcom + pycom)
        height_float = ratio * width
        height = math.ceil(height_float)

    real_ratio = (horizontal_height + z) / (pxcom + pycom)
    real_height_float = real_ratio * width
    z = z / (pxcom + pycom) * width

    delta = height - real_height_float

    return height, delta, z


class LazyAlternativeSprites(grf.AlternativeSprites):
    def __init__(self, voxel, part, kwargs=None, *sprites):
        super().__init__(*sprites)
        from .voxel import LazyVoxel

        assert isinstance(voxel, LazyVoxel)
        self.voxel = voxel
        self.part = part
        self.kwargs = kwargs or {}

    def get_sprite(self, *, zoom=None, bpp=None):
        self.voxel.render()
        return super().get_sprite(zoom=zoom, bpp=bpp)

    def get_fingerprint(self):
        return {"name": self.voxel.name, "part": self.part, "prefix": self.voxel.prefix}

    def get_resources(self):
        self.voxel.render()
        return super().get_resources()

    def get_resource_files(self):
        self.voxel.render()
        return super().get_resource_files()

    def __repr__(self):
        return f"LazyAlternativeSprites<{self.voxel.name}:{self.part}>"

    @functools.cache
    def squash(self, ratio):
        squashed_voxel = self.voxel.squash(ratio, "squashed")
        return squashed_voxel.spritesheet(**self.kwargs)[self.part]


class CustomCropMixin:
    def __init__(self, *args, fixed_crop=False, crop_amount=(0, 0), **kw):
        super().__init__(*args, **kw)
        self.fixed_crop = fixed_crop
        self.crop_amount = crop_amount

    def _do_crop(self, context, w, h, rgb, alpha, mask):
        crop_x = crop_y = 0
        if self.fixed_crop:
            crop_x, crop_y = self.crop_amount

            timer = context.start_timer()
            if alpha is not None:
                cols_bitset = alpha.any(0)
                rows_bitset = alpha.any(1)
            elif rgb is not None:
                cols_bitset = rgb.any((0, 2))
                rows_bitset = rgb.any((1, 2))
            elif mask is not None:
                cols_bitset = mask.any(0)
                rows_bitset = mask.any(1)
            else:
                raise context.failure(self, "All data layers are None")

            cols_used = np.arange(w)[cols_bitset]
            rows_used = np.arange(h)[rows_bitset]

            w = max(cols_used, default=0) - crop_x + 1
            h = max(rows_used, default=0) - crop_y + 1

            if rgb is not None:
                rgb = rgb[crop_y : crop_y + h, crop_x : crop_x + w]
            if alpha is not None:
                alpha = alpha[crop_y : crop_y + h, crop_x : crop_x + w]
            if mask is not None:
                mask = mask[crop_y : crop_y + h, crop_x : crop_x + w]

            timer.count_custom("Cropping sprites")
        elif self.crop:
            return super()._do_crop(context, w, h, rgb, alpha, mask)

        return crop_x, crop_y, w, h, rgb, alpha, mask

    def get_resource_files(self):
        return super().get_resource_files() + (THIS_FILE,)


class CustomCropFileSprite(CustomCropMixin, grf.FileSprite):
    pass


class CustomCropWithMask(CustomCropMixin, grf.WithMask):
    pass


def spritesheet_template(
    voxel,
    path,
    dimens,
    angles,
    bbox,
    deltas,
    ydeltas,
    offsets,
    yoffsets,
    z_scale,
    bbox_joggle=None,
    bpps=(8, 32),
    scales=(1, 2, 4),
    xdiff=0,
    ydiff=0,
    shift=0,
    road_mode=False,
    manual_crop=None,
    childsprite=False,
    relative_childsprite=False,
    kwargs=None,
):
    guessed_dimens = []
    for i in range(len(dimens)):
        x, y = dimens[i]
        y, z_ydiff, z_height = guess_dimens(x, y, angles[i], bbox, z_scale)
        guessed_dimens.append((x, y, z_ydiff, z_height))

    kwargs = kwargs or {}
    oxdiff = kwargs["xdiff"]
    oxspan = kwargs["xspan"]
    oydiff = kwargs["ydiff"]
    oyspan = kwargs["yspan"]

    def get_rels(direction, scale):
        w, h, z_ydiff, z_height = map(lambda a: a * scale, guessed_dimens[direction])
        if road_mode:
            xrel = -((w - 1) // (scale * 2) * scale + 1)
        else:
            # XXX
            # Actually, this is unverified legacy code
            # Vehicle people have much disagreement with what's the right offset anyways...
            xrel = -w / 2
        if road_mode:
            yrel = -z_height
        else:
            yrel = -h / 2

        xrel += xdiff * scale
        yrel += ydiff * scale
        yrel -= z_ydiff

        if oxdiff != 0:
            xrel += deltas[direction][0] * oxdiff * scale
            yrel += deltas[direction][1] * oxdiff * scale

        if road_mode and oxspan != 16:
            offset = 16 - oxspan
            xrel += offsets[direction][0] * offset * scale
            yrel += offsets[direction][1] * offset * scale

        if oydiff != 0:
            xrel += ydeltas[direction][0] * oydiff * scale
            yrel += ydeltas[direction][1] * oydiff * scale

        if road_mode and oyspan != 16:
            offset = 16 - oyspan
            xrel += yoffsets[direction][0] * offset * scale
            yrel += yoffsets[direction][1] * offset * scale

        if bbox_joggle is not None:
            xrel += bbox_joggle[direction][0] * scale
            yrel += bbox_joggle[direction][1] * scale

        return int(xrel + 0.5), int(yrel + 0.5)

    def with_optional_mask(sprite, mask):
        if mask is None:
            return sprite
        return CustomCropWithMask(sprite, mask, fixed_crop=sprite.fixed_crop, crop_amount=sprite.crop_amount)

    return [
        LazyAlternativeSprites(
            voxel,
            idx,
            kwargs,
            *(
                with_optional_mask(
                    CustomCropFileSprite(
                        make_image_file(f"{path}_{scale}x_{bpp}bpp.png"),
                        (sum(guessed_dimens[j][0] for j in range(i)) + i * 8) * scale,
                        0,
                        guessed_dimens[i][0] * scale,
                        guessed_dimens[i][1] * scale,
                        xofs=(
                            get_rels(i, scale)[0] - relative_childsprite[0] * scale
                            if relative_childsprite
                            else childsprite[0] * scale if childsprite else get_rels(i, scale)[0]
                        ),
                        yofs=(
                            get_rels(i, scale)[1] - relative_childsprite[1] * scale
                            if relative_childsprite
                            else childsprite[1] * scale if childsprite else get_rels(i, scale)[1]
                        ),
                        bpp=bpp,
                        zoom=SCALE_TO_ZOOM[scale],
                        **(
                            {}
                            if manual_crop is None
                            else {"fixed_crop": True, "crop_amount": (manual_crop[0] * scale, manual_crop[1] * scale)}
                        ),
                    ),
                    (
                        CustomCropFileSprite(
                            make_image_file(f"{path}_{scale}x_mask.png"),
                            (sum(guessed_dimens[j][0] for j in range(i)) + i * 8) * scale,
                            0,
                            guessed_dimens[i][0] * scale,
                            guessed_dimens[i][1] * scale,
                        )
                        if bpp == 32
                        else None
                    ),
                )
                for bpp in bpps
                for scale in scales
            ),
        )
        for idx in range(len(dimens))
        if (i := (idx + shift) % len(dimens)) or True
    ]
