import grf
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from agrf.pkg import load_font

THIS_FILE = grf.PythonFile(__file__)


class NumberedSprite(grf.Sprite):
    def __init__(self, sprite, number):
        self.sprite = sprite
        self.number = number

    @property
    def default_name(self):
        return f"{self.sprite.default_name} #{self.number}"

    def prepare_files(self):
        self.sprite.prepare_files()

    def get_data_layers(self, context):
        w, h, rgb, alpha, mask = self.sprite.get_data_layers(context)
        if rgb is not None:
            img = Image.fromarray(rgb)
            alpha = Image.fromarray(alpha)
            draw = ImageDraw.Draw(img)
            drawa = ImageDraw.Draw(alpha)
            font = load_font("resources/fonts/AntaeusConsoleNumbers.otf", w // 4)
            message = str(self.number)
            _, _, _w, _h = draw.textbbox((0, 0), message, font=font)
            draw.text(((w - _w) // 2, w // 4), message, "blue", font=font)
            drawa.text(((w - _w) // 2, w // 4), message, 255, font=font)
            rgb = np.asarray(img)
            alpha = np.asarray(alpha)
        return w, h, rgb, alpha, mask

    def get_image_files(self):
        return self.sprite.get_image_files()

    def get_fingerprint(self):
        return grf.combine_fingerprint(
            super().get_fingerprint_base(), sprite=self.sprite.get_fingerprint(), number=self.number
        )

    def get_resource_files(self):
        return super().get_resource_files() + (THIS_FILE,) + self.sprite.get_resource_files()

    def __getattr__(self, name):
        return getattr(self.sprite, name)


def number_alternatives(a, number):
    return grf.AlternativeSprites(*[NumberedSprite(x, number) for x in a.sprites])
