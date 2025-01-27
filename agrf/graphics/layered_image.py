import grf
import numpy as np
from .palette import NUMPY_PALETTE
from PIL import Image


# An intermediate representation of image, based on grf.Sprite.get_data_layers()
# Most non-IO methods are in-place for `self` for performance purposes, but will not change `other`
class LayeredImage:
    def __init__(self, xofs, yofs, w, h, rgb, alpha, mask):
        self.xofs = xofs
        self.yofs = yofs
        self.w = w
        self.h = h
        self.rgb = rgb
        self.alpha = alpha
        self.mask = mask

    @staticmethod
    def empty():
        return LayeredImage(0, 0, 0, 0, None, None, None)

    @staticmethod
    def canvas(xofs, yofs, w, h, bpp=32, has_mask=True):
        return LayeredImage(
            xofs,
            yofs,
            w,
            h,
            np.zeros((h, w, 3), dtype=np.uint8) if bpp == 32 else None,
            np.zeros((h, w), dtype=np.uint8) if bpp == 32 else None,
            np.zeros((h, w), dtype=np.uint8) if has_mask else None,
        )

    @staticmethod
    def from_sprite(sprite, context=None):
        context = context or grf.DummyWriteContext()
        w, h, rgb, alpha, mask = sprite.get_data_layers(context)
        return LayeredImage(sprite.xofs, sprite.yofs, w, h, rgb, alpha, mask)

    def copy(self):
        return LayeredImage(
            self.xofs,
            self.yofs,
            self.w,
            self.h,
            None if self.rgb is None else self.rgb.copy(),
            None if self.alpha is None else self.alpha.copy(),
            None if self.mask is None else self.mask.copy(),
        )

    def copy_from(self, other):
        self.xofs = other.xofs
        self.yofs = other.yofs
        self.w = other.w
        self.h = other.h
        self.rgb = None if other.rgb is None else other.rgb.copy()
        self.alpha = None if other.alpha is None else other.alpha.copy()
        self.mask = None if other.mask is None else other.mask.copy()

        return self

    def apply_mask(self):
        if self.rgb is None or self.mask is None:
            return
        v = np.min(self.rgb, axis=2, keepdims=True)
        mask_colour = NUMPY_PALETTE[self.mask].astype(np.uint16)
        mask_colour *= v
        mask_colour //= 2**7
        r_ob = np.maximum(mask_colour[:, :, 0], 255) - 255
        g_ob = np.maximum(mask_colour[:, :, 1], 255) - 255
        b_ob = np.maximum(mask_colour[:, :, 2], 255) - 255
        ob = (r_ob + g_ob + b_ob) // 2

        above = mask_colour >= 255
        below = np.minimum(mask_colour + ob[:, :, np.newaxis] * (255 - mask_colour) // 256, 255).astype(np.uint8)
        mixed = np.where(above, 255, below)

        mask_pal = self.mask == 0
        blended = np.where(np.broadcast_to(mask_pal[:, :, np.newaxis], (*mask_pal.shape, 3)), self.rgb, mixed)

        self.rgb = blended
        self.mask = None

        return self

    def adjust_canvas(self, other, childsprite=None):
        w = max(other.w + other.xofs - self.xofs, self.w) - min(0, other.xofs - self.xofs)
        h = max(other.h + other.yofs - self.yofs, self.h) - min(0, other.yofs - self.yofs)
        x0 = max(0, self.xofs - other.xofs)
        y0 = max(0, self.yofs - other.yofs)

        if w == self.w and h == self.h:
            if self.rgb is None and other.rgb is not None:
                self.rgb = np.zeros((h, w, 3), dtype=np.uint8)
            if self.alpha is None and other.alpha is not None:
                self.alpha = np.zeros((h, w), dtype=np.uint8)
            if self.mask is None and other.mask is not None:
                self.mask = np.zeros((h, w), dtype=np.uint8)
            return

        if self.rgb is not None:
            new_rgb = np.zeros((h, w, 3), dtype=np.uint8)
            new_rgb[y0 : y0 + self.h, x0 : x0 + self.w] = self.rgb
            self.rgb = new_rgb
        elif other.rgb is not None:
            self.rgb = np.zeros((h, w, 3), dtype=np.uint8)

        if self.alpha is not None:
            new_alpha = np.zeros((h, w), dtype=np.uint8)
            new_alpha[y0 : y0 + self.h, x0 : x0 + self.w] = self.alpha
            self.alpha = new_alpha
        elif other.rgb is not None:
            self.alpha = np.zeros((h, w), dtype=np.uint8)

        if self.mask is not None:
            new_mask = np.zeros((h, w), dtype=np.uint8)
            new_mask[y0 : y0 + self.h, x0 : x0 + self.w] = self.mask
            self.mask = new_mask
        elif other.rgb is not None:
            self.mask = np.zeros((h, w), dtype=np.uint8)

        self.w = w
        self.h = h
        self.xofs -= x0
        self.yofs -= y0

        return self

    @staticmethod
    def _crop_if_childsprite(a, b, childsprite):
        if childsprite:
            return a[: b.shape[0], : b.shape[1]]
        return a

    def blend_over(self, other, childsprite=False):
        if other.rgb is None and other.mask is None:
            return
        if self.rgb is None and self.mask is None:
            self.copy_from(other)
            return
        if childsprite:
            x1 = 0
            y1 = 0
        else:
            self.adjust_canvas(other)

            x1 = other.xofs - self.xofs
            y1 = other.yofs - self.yofs

        if self.mask is not None:
            mask_viewport = self.mask[y1 : y1 + other.h, x1 : x1 + other.w]
            if self.rgb is None:
                opacity = other.mask != 0
            else:
                opacity = other.alpha != 0
            if other.mask is None:
                mask_viewport[:, :] = mask_viewport * (1 - opacity)
            else:
                mask_viewport[:, :] = (
                    mask_viewport * (1 - opacity)
                    + self._crop_if_childsprite(other.mask, mask_viewport, childsprite) * opacity
                )

        if self.rgb is not None:
            rgb_viewport = self.rgb[y1 : y1 + other.h, x1 : x1 + other.w]
            alpha_viewport = self.alpha[y1 : y1 + other.h, x1 : x1 + other.w]

            alpha1 = alpha_viewport.astype(np.uint32)
            alpha2 = self._crop_if_childsprite(other.alpha, alpha1, childsprite).astype(np.uint32)
            alpha1_component = np.expand_dims(alpha1 * (255 - alpha2), 2)
            alpha2_component = np.expand_dims(alpha2 * 255, 2)
            new_alpha = alpha1_component + alpha2_component
            rgb_viewport[:, :] = (
                alpha1_component * rgb_viewport
                + alpha2_component * self._crop_if_childsprite(other.rgb, rgb_viewport, childsprite)
                + new_alpha // 2
            ) // np.maximum(new_alpha, 1)
            alpha_viewport[:, :] = (new_alpha[:, :, 0] + 128) // 255

        return self

    def move(self, offset_x, offset_y):
        self.xofs += offset_x
        self.yofs += offset_y
        return self

    def remap(self, remap):
        if self.mask is not None:
            self.mask = remap.remap_array(self.mask)
        return self

    def crop(self):
        if self.alpha is not None:
            cols_bitset = self.alpha.any(0)
            rows_bitset = self.alpha.any(1)
        elif self.rgb is not None:
            cols_bitset = self.rgb.any((0, 2))
            rows_bitset = self.rgb.any((1, 2))
        elif self.mask is not None:
            cols_bitset = self.mask.any(0)
            rows_bitset = self.mask.any(1)
        else:
            raise Exception("All data layers are None")

        cols_used = np.arange(self.w)[cols_bitset]
        rows_used = np.arange(self.h)[rows_bitset]

        crop_x = min(cols_used, default=0)
        crop_y = min(rows_used, default=0)
        w = max(cols_used, default=0) - crop_x + 1
        h = max(rows_used, default=0) - crop_y + 1

        if self.rgb is not None:
            self.rgb = self.rgb[crop_y : crop_y + h, crop_x : crop_x + w]
        if self.alpha is not None:
            self.alpha = self.alpha[crop_y : crop_y + h, crop_x : crop_x + w]
        if self.mask is not None:
            self.mask = self.mask[crop_y : crop_y + h, crop_x : crop_x + w]
        self.w = w
        self.h = h
        self.xofs += crop_x
        self.yofs += crop_y

        return self

    def to_image(self):
        if self.mask is not None:
            self.apply_mask()
        return np.concatenate((self.rgb, self.alpha[:, :, np.newaxis]), axis=2)

    def to_pil_image(self):
        return Image.fromarray(self.to_image())

    # Keep aspect ratio
    # Using given w and h as maximum
    # offsets updated approximately
    def resize(self, w, h):
        metadata_updated = False
        for k in ["rgb", "alpha", "mask"]:
            img = getattr(self, k)
            if img is None:
                continue
            old_w, old_h = img.shape[1], img.shape[0]
            img = Image.fromarray(img)
            img.thumbnail((w, h), Image.Resampling.NEAREST if k == "mask" else Image.Resampling.LANCZOS)
            img = np.asarray(img)
            setattr(self, k, img)
            new_w, new_h = img.shape[1], img.shape[0]
            if not metadata_updated:
                self.w = new_w
                self.h = new_h
                self.xofs = (self.xofs * new_w + old_w // 2) // old_w
                self.yofs = (self.yofs * new_h + old_h // 2) // old_h
                metadata_updated = True
        return self

    def to_rgb(self):
        if self.rgb is not None:
            return self
        self.rgb = NUMPY_PALETTE[self.mask]
        self.alpha = (self.mask != 0).astype(np.uint8) * 255
        self.mask = None

        return self
