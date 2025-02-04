import json
import hashlib
from agrf.magic import Switch

switch_cache = {}


def switch_fingerprint(s):
    if isinstance(s, int):
        return s
    return {
        "ranges": list(sorted([(r.low, r.high, switch_fingerprint(r.ref)) for r in s._ranges])),
        "default": switch_fingerprint(s.default),
        "code": s.code,
    }


def switch_hash(s):
    return hashlib.sha384(json.dumps(switch_fingerprint(s), sort_keys=True).encode()).hexdigest()


def make_switch(ranges, default, code):
    ret = Switch(ranges=ranges, default=default, code=code)
    h = switch_hash(ret)
    if h in switch_cache:
        return switch_cache[h]
    switch_cache[h] = ret
    return ret
