import grf
from .functor import CachedFunctorMixin


class Switch(CachedFunctorMixin, grf.Switch):
    def __init__(self, code, ranges, default, *, feature=None, ref_id=None, related_scope=False, subroutines=None):
        super().__init__(
            code, ranges, default, feature=feature, ref_id=ref_id, related_scope=related_scope, subroutines=subroutines
        )

    def fmap(self, f):
        return type(self)(
            self.code,
            {(r.low, r.high): f(r.ref) for r in self._ranges},
            f(self.default),
            feature=self.feature,
            ref_id=self.ref_id,
            related_scope=self.related_scope,
            subroutines=self.subroutines,
        )

    def lookup(self, x):
        for r in self._ranges:
            if r.low <= x <= r.high:
                return r.ref
        return self.default

    # FIXME: should probably be refactored into something more general
    # and not rely on everything else implementing `get_default_graphics`
    def get_default_graphics(self):
        return self.default.get_default_graphics()


class DualCallback(CachedFunctorMixin, grf.DualCallback):
    def __init__(self, default, purchase=None):
        super().__init__(default, purchase)

    def fmap(self, f):
        return DualCallback(f(self.default), f(self.purchase) if self.purchase is not None else None)
