import grf
from agrf.actions import FakeReferencingAction, FakeReferencedAction
from agrf.lib.building.registers import code, default_code
from agrf.lib.building.station_tile_switch import StationTileSwitch
from agrf.strings import label_printable
from agrf.utils import unique


class AStation(grf.SpriteGenerator):
    def __init__(
        self,
        *,
        id,
        translation_name,
        layouts,
        callbacks=None,
        non_traversable_tiles=0x0,
        is_waypoint=False,
        doc_layout=None,
        enable_if=None,
        make_foundation=False,
        foundation_object=None,
        extra_code="",
        action2_pool=None,
        station_tile_switch_class=None,
        **props,
    ):
        super().__init__()
        self.id = id
        self.translation_name = translation_name
        self.layouts = layouts
        if callbacks is None:
            callbacks = {}
        self.callbacks = grf.make_callback_manager(grf.STATION, callbacks)
        self.is_waypoint = is_waypoint
        self.doc_layout = doc_layout
        self.enable_if = enable_if
        self.make_foundation = make_foundation
        self.foundation_object = foundation_object
        self.extra_code = extra_code
        self.action2_pool = action2_pool
        self._station_tile_switch_class = station_tile_switch_class
        self._props = {
            **props,
            "non_traversable_tiles": non_traversable_tiles,
            "draw_pylon_tiles": 0xFF ^ non_traversable_tiles,
            "hide_wire_tiles": non_traversable_tiles,
        }

    @property
    def class_label_plain(self):
        return label_printable(self._props["class_label"])

    def _is_station_tile_switch(self, obj):
        return self._station_tile_switch_class is not None and isinstance(obj, self._station_tile_switch_class)

    def _map_foundation(self, obj):
        if self._is_station_tile_switch(obj):
            return obj.to_index(None)
        return obj

    def get_sprites(self, g, sprites=None):
        is_managed_by_metastation = sprites is not None
        if isinstance(self.translation_name, str):
            translated_name = g.strings[f"STR_STATION_{self.translation_name}"]
        elif callable(self.translation_name):
            translated_name = self.translation_name(g.strings)
        else:
            raise TypeError(f"translation_name must be a string or callable, got {type(self.translation_name)}")

        extra_props = {"station_name": g.strings.add(translated_name).get_persistent_id()}
        if not self.is_waypoint:
            extra_props["station_class_name"] = g.strings.add(
                g.strings[f"STR_STATION_CLASS_{self.class_label_plain}"]
            ).get_persistent_id()

        res = []

        if self.action2_pool is not None:
            graphics = self.action2_pool.get_action_2_zero()
        else:
            graphics = grf.GenericSpriteLayout(ent1=[0], ent2=[0], feature=grf.STATION)

        props = self._props.copy()

        use_foundation = self.make_foundation or self.foundation_object is not None

        if use_foundation and self.action2_pool is not None:
            if self.make_foundation:
                cb14 = self.callbacks.select_sprite_layout.default
                self.callbacks.select_sprite_layout.default = cb14.to_index(self.layouts)
                foundations = self.action2_pool.map_switch(cb14)
                foundations = self._map_foundation(foundations)
            else:  # foundation_object
                if self.foundation_object is self.foundation_object.M:
                    foundation_object_list = [self.foundation_object]
                else:
                    foundation_object_list = [self.foundation_object, self.foundation_object.M]

                foundation_list = [
                    self.action2_pool.map_foundation_switch(x.to_switch()) for x in foundation_object_list
                ]
                foundation_list = [self._map_foundation(x) for x in foundation_list]

                if len(foundation_list) == 1:
                    foundations = foundation_list[0]
                else:
                    foundations = grf.Switch(
                        ranges={1: foundation_list[1]}, code="extra_callback_info2 % 2", default=foundation_list[0]
                    )

            self.callbacks.graphics = grf.GraphicsCallback(
                default=grf.Switch(
                    ranges={2: foundations},
                    code=code + self.extra_code + default_code + "\nextra_callback_info1_byte",
                    default=graphics,
                ),
                purchase=grf.Switch(ranges={0: graphics}, code=code + self.extra_code, default=graphics),
            )
            props["general_flags"] = props.get("general_flags", 0) | 0b1000
        else:
            self.callbacks.graphics = grf.Switch(
                ranges={0: graphics}, code=code + self.extra_code + default_code, default=graphics
            )

        cb_props = {}
        self.callbacks.set_flag_props(cb_props)

        if not is_managed_by_metastation:
            sprites = self.sprites
            res.append(grf.Action1(feature=grf.STATION, set_count=1, sprite_count=len(self.sprites)))

            for s in self.sprites:
                res.append(s)

        if self.id >= 0xFF:
            res.append(grf.If(is_static=False, variable=0xA1, condition=0x04, value=0x1E000000, skip=255, varsize=4))
        if self.enable_if:
            for cond in self.enable_if:
                res.append(cond.make_if(is_static=False, skip=255))
        res.append(
            definition := grf.Define(
                feature=grf.STATION,
                id=self.id,
                props={
                    "class_label": (b"WAYP" if self.is_waypoint else props["class_label"]),
                    "advanced_layout": grf.SpriteLayoutList([l.to_grf(sprites) for l in self.layouts]),
                    **{k: v for k, v in props.items() if k != "class_label"},
                    **cb_props,
                    **(extra_props if self.id >= 0xFF else {}),
                },
            )
        )
        if self.id >= 0xFF or self.enable_if:
            res.append(grf.Label(255, bytes()))

        if self.is_waypoint:
            openttd_15_props = {
                "class_label": b"\xff" + self._props["class_label"][1:],
                "station_class_name": g.strings.add(
                    g.strings[f"STR_STATION_CLASS_{self.class_label_plain}"]
                ).get_persistent_id(),
            }
            res.append(grf.If(is_static=False, variable=0xA1, condition=0x04, value=0x1F000000, skip=1, varsize=4))
            res.append(grf.Define(feature=grf.STATION, id=self.id, props=openttd_15_props))

        [map_action] = self.callbacks.make_map_action(definition)
        if self.id >= 0xFF:
            if_action = FakeReferencedAction(
                grf.If(is_static=False, variable=0xA1, condition=0x04, value=0x1E000000, skip=1, varsize=4), grf.STATION
            )
            map_action = FakeReferencingAction(map_action, [if_action])
        res.append(map_action)

        if self.id < 0xFF:
            class_name = g.strings[f"STR_STATION_CLASS_{self.class_label_plain}"]
            res.extend(class_name.get_actions(grf.STATION, 0xC400 + self.id, is_generic_offset=True))
            res.extend(translated_name.get_actions(grf.STATION, 0xC500 + self.id, is_generic_offset=True))

        return res

    @property
    def sprites(self):
        return unique(sub for l in self.layouts for sub in l.sprites)
