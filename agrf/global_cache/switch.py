import grf
from agrf.magic import Switch
from agrf.lib.building.foundation import Foundation
from .digest import digest

switch_cache = {}


def switch_fingerprint(s):
    if isinstance(s, int):
        return s
    if isinstance(s, grf.GenericSpriteLayout):
        return {"feature": str(s.feature), "ent1": s.ent1, "ent2": s.ent2}
    if isinstance(s, Foundation):
        return {"feature": "foundation", "foundation": s.get_fingerprint()}
    return {
        "ranges": list(sorted([(r.low, r.high, switch_fingerprint(r.ref)) for r in s._ranges])),
        "default": switch_fingerprint(s.default),
        "code": s.code,
    }


def switch_hash(s):
    return digest(switch_fingerprint(s))


def make_switch(ranges, default, code):
    ret = Switch(ranges=ranges, default=default, code=code)
    h = switch_hash(ret)
    if h in switch_cache:
        return switch_cache[h]
    switch_cache[h] = ret
    return ret
