class AVariant(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def modified_copy(self, *, variants=[], **kwargs):
        return type(self)(**{**self, "variants": variants, **kwargs})

    def apply(self):
        return self["real_class"](**{k: v for k, v in self.items() if k not in ["variants", "real_class"]})

    def list_variants(self):
        ret = [self.modified_copy()]
        if self.get("variants") is not None:
            for v in self["variants"]:
                ret.extend(self.modified_copy(**v).list_variants())
        return ret

    def get_variants(self):
        return [v.apply() for v in self.list_variants()]

    def __hash__(self):
        return id(self)

    def __getattr__(self, name):
        return self.__dict__[name]
