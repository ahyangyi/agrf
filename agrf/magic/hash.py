from functools import wraps
import inspect
from typing import Callable, Any


def make_hashable_arg(*, arg_name: str, hash_fn: Callable[[Any], int], eq_fn: Callable[[Any, Any], bool]):
    """
    Decorator that converts *arg_name* into a hashable proxy
    using the caller-supplied (hash_fn, eq_fn) pair.
    No caching is applied here – combine with any @cache you like.
    """

    def decorator(func):
        sig = inspect.signature(func)
        if arg_name not in sig.parameters:
            raise ValueError(f"{arg_name!r} is not a parameter of {func.__name__}")

        class _HashableProxy:
            __slots__ = ("_obj", "_hash")

            def __init__(self, obj):
                self._obj = obj
                self._hash = hash_fn(obj)

            def __hash__(self):
                return self._hash

            def __eq__(self, other):
                if not isinstance(other, _HashableProxy):
                    return NotImplemented
                return eq_fn(self._obj, other._obj)

            def __getattr__(self, name):
                return getattr(self._obj, name)

        @wraps(func)
        def _wrapper(*args, **kwargs):
            ba = sig.bind(*args, **kwargs)
            ba.apply_defaults()
            ba.arguments[arg_name] = _HashableProxy(ba.arguments[arg_name])
            return func(*ba.args, **ba.kwargs)

        return _wrapper

    return decorator
