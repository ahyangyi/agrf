import grf


class RoadTypeBase(grf.SpriteGenerator):
    def __init__(self, *, id, feature, underlay=None, overlay=None, **props):
        super().__init__()
        self.id = id
        self.feature = feature
        self.underlay = underlay
        self.overlay = overlay
        self._props = props

    def get_sprites(self, g):
        extra_props = {}
        for p in [
            "toolbar_caption",
            "menu_text",
            "build_window_caption",
            "autoreplace_text",
            "new_engine_text",
            "name",
        ]:
            if self._props.get(p):
                s = self._props[p]
                if isinstance(s, grf.StringRef):
                    extra_props[p] = s.get_persistent_id()
                else:
                    extra_props[p] = g.strings.add(s).get_persistent_id()

        res = []
        res.append(definition := grf.Define(feature=self.feature, id=self.id, props={**self._props, **extra_props}))

        layouts = []
        maps = {}

        if self.overlay:
            i = len(layouts)
            layouts.append(grf.GenericSpriteLayout(ent1=(i,), ent2=(i,), feature=self.feature))
            maps[0x01] = layouts[i]
            res.append(grf.Action1(feature=self.feature, set_count=1, sprite_count=19, first_set=i))
            for s in self.overlay:
                res.append(s)
        if self.underlay:
            i = len(layouts)
            layouts.append(grf.GenericSpriteLayout(ent1=(i,), ent2=(i,), feature=self.feature))
            maps[0x02] = layouts[i]
            res.append(grf.Action1(feature=self.feature, set_count=1, sprite_count=19, first_set=i))
            for s in self.underlay:
                res.append(s)

        res.append(grf.Map(definition=definition, maps=maps, default=layouts[0]))

        return res


class RoadType(RoadTypeBase):
    def __init__(self, *, id, **kwargs):
        super().__init__(id=id, feature=grf.ROADTYPE, **kwargs)


class TramType(RoadTypeBase):
    def __init__(self, *, id, **kwargs):
        super().__init__(id=id, feature=grf.TRAMTYPE, **kwargs)
