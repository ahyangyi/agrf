from collections.abc import Collection, Mapping, Hashable


def deep_freeze(thing):
    if thing is None or isinstance(thing, str):
        return thing
    elif isinstance(thing, Mapping):
        return tuple((k, deep_freeze(v)) for k, v in sorted(thing.items()))
    elif isinstance(thing, Collection):
        return tuple(deep_freeze(i) for i in thing)
    elif not isinstance(thing, Hashable):
        raise TypeError(f"unfreezable type: '{type(thing)}'")
    else:
        return thing


class CachedFunctorMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attr_cache = {}
        self.call_cache = {}

    def fmap(self, f):
        raise NotImplementedError()

    def __getattr__(self, name):
        if name in self.attr_cache:
            return self.attr_cache[name]
        ret = self.fmap(lambda x: getattr(x, name))
        self.attr_cache[name] = ret
        return ret

    def __call__(self, *args, **kwargs):
        key = deep_freeze((args, kwargs))
        if key in self.call_cache:
            return self.call_cache[key]
        ret = self.fmap(lambda x: x(*args, **kwargs))
        self.call_cache[key] = ret
        return ret


class TaggedCachedFunctorMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attr_cache = {}
        self.call_cache = {}

    def fmap(self, f, method_name):
        raise NotImplementedError()

    def __getattr__(self, name):
        if name in self.attr_cache:
            return self.attr_cache[name]
        ret = self.fmap(lambda x: getattr(x, name), name)
        ret.__last_getattr = name
        self.attr_cache[name] = ret
        return ret

    def __call__(self, *args, **kwargs):
        key = deep_freeze((args, kwargs))
        if key in self.call_cache:
            return self.call_cache[key]
        ret = self.fmap(lambda x: x(*args, **kwargs), self.__last_getattr)
        self.call_cache[key] = ret
        return ret
