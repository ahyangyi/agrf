import json
import hashlib
import grf
from agrf.magic import Switch
from agrf.lib.building.foundation import Foundation
from .pool import dedup


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
    return hashlib.sha384(json.dumps(switch_fingerprint(s), sort_keys=True).encode()).hexdigest()


def switch_eq(a, b):
    return switch_fingerprint(a) == switch_fingerprint(b)


def make_switch(ranges, default, code):
    return dedup(Switch(ranges=ranges, default=default, code=code), hash_fn=switch_hash, eq_fn=switch_eq)
