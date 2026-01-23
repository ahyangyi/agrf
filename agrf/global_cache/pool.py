__POOL__ = {}


def dedup(obj, hash_fn=lambda x: hash(x), eq_fn=lambda x, y: x == y):
    key = hash_fn(obj)
    if key not in __POOL__:
        __POOL__[key] = [obj]
        return obj

    for elem in __POOL__[key]:
        if eq_fn(obj, elem):
            return elem

    __POOL__[key].append(obj)
    return obj
