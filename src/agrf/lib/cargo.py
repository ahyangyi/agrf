import grf


class Cargo(grf.SpriteGenerator):
    def __init__(self, id, **props):
        self.id = id
        self._props = props
        self.callbacks = grf.make_callback_manager(grf.CARGO, {})

    @staticmethod
    def translate_strings(props, g):
        props = props.copy()
        for p in ["type_name", "unit_name", "one_text", "many_text", "type_abbreviation"]:
            if props.get(p):
                s = props[p]
                if isinstance(s, grf.StringRef):
                    props[p] = s.get_persistent_id()
                else:
                    props[p] = g.strings.add(s).get_persistent_id()
        return props

    def get_definitions(self, g):
        return [grf.Define(feature=grf.CARGO, id=self.id, props=Cargo.translate_strings(self._props, g))]

    def get_sprites(self, g):
        res = self.get_definitions(g)
        if len(res) == 0:
            return []
        definition = res[-1]
        self.callbacks.graphics = 0
        res.extend(self.callbacks.make_map_action(definition))

        return res
