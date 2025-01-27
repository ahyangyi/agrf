import io
import pkgutil
import json
from PIL import Image, ImageFont


def load_third_party_image(path):
    content = pkgutil.get_data("agrf", path)
    f = io.BytesIO(content)
    return Image.open(f)


def load_font(path, size):
    content = pkgutil.get_data("agrf", path)
    f = io.BytesIO(content)
    return ImageFont.truetype(f, size)


def load_json(path):
    content = pkgutil.get_data("agrf", path)
    f = io.BytesIO(content)
    return json.load(f)
