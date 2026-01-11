from agrf.graphics.sprites.foundation import FoundationSprite
from .digest import digest

CACHE = {}


def make_foundation_sprite(*args, **kwargs):
    ret = FoundationSprite(*args, **kwargs)
    dig = digest(ret.get_fingerprint())

    if dig not in CACHE:
        CACHE[dig] = ret
    return CACHE[dig]
