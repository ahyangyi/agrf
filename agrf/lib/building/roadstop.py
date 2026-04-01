import grf
from agrf.magic import Switch
from agrf.strings import label_printable

from agrf.utils import unique


class ARoadStop(grf.SpriteGenerator):
    def __init__(
        self,
        *,
        id,
        translation_name,
        graphics,
        callbacks=None,
        doc_layout=None,
        is_waypoint=False,
        enable_if=None,
        **props,
    ):
        super().__init__()
        self.id = id
        self.translation_name = translation_name
        self.graphics = graphics
        if callbacks is None:
            callbacks = {}
        self.callbacks = grf.make_callback_manager(grf.ROAD_STOP, callbacks)
        self.doc_layout = doc_layout
        self.is_waypoint = is_waypoint
        self.enable_if = enable_if
        self._props = props

    @property
    def class_label_plain(self):
        return label_printable(self._props["class_label"])

    def get_sprites(self, g, sprites=None):
        res = []

        extra_props = {
            "name_id": g.strings.add(g.strings[f"STR_ROADSTOP_{self.translation_name}"]).get_persistent_id(),
            "class_name_id": g.strings.add(
                g.strings[f"STR_ROADSTOP_CLASS_{self.class_label_plain}"]
            ).get_persistent_id(),
        }

        if sprites is None:
            sprites = self.sprites
            if len(sprites) > 0:
                res.append(grf.Action1(feature=grf.ROAD_STOP, set_count=len(self.sprites), sprite_count=1))

                for s in self.sprites:
                    res.append(s)

        graphics = self.graphics.to_action2(feature=grf.ROAD_STOP, sprite_list=sprites)
        self.callbacks.graphics = Switch(
            ranges={0: graphics},
            default=graphics,
            code="""
TEMP[0x03] = (terrain_type & 0x4) == 0x4
TEMP[0x07] = (19 * ((terrain_type & 0x5) > 0))
""",
        )
        self.callbacks.set_flag_props(self._props)

        if self.is_waypoint:
            class_label = b"\xff" + self._props["class_label"][1:]
        else:
            class_label = self._props["class_label"]

        res.append(grf.If(is_static=True, variable=0xA1, condition=0x04, value=0x1E000000, skip=255, varsize=4))
        if self.is_waypoint:
            res.append(grf.If(is_static=True, variable=0xA1, condition=0x04, value=0x1F000000, skip=255, varsize=4))
        if self.enable_if:
            for cond in self.enable_if:
                res.append(cond.make_if(is_static=False, skip=255))

        res.append(
            definition := grf.Define(
                feature=grf.ROAD_STOP,
                id=self.id,
                props={
                    "class_label": class_label,
                    **{k: v for k, v in self._props.items() if k != "class_label"},
                    **extra_props,
                },
            )
        )
        res.append(grf.Label(255, bytes()))

        res.extend(self.callbacks.make_map_action(definition))

        return res

    @property
    def sprites(self):
        return unique(sub for l in self.graphics._ranges for sub in l.ref.sprites)
