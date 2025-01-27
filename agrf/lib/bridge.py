import grf
from dataclasses import dataclass
from typing import Tuple


@dataclass
class SpritePair:
    X: grf.SpriteRef | grf.ResourceAction
    Y: grf.SpriteRef | grf.ResourceAction


@dataclass
class SingleTypeBridgeLayout:
    back: Tuple[SpritePair, SpritePair, SpritePair, SpritePair, SpritePair, SpritePair]
    front: Tuple[SpritePair, SpritePair, SpritePair, SpritePair, SpritePair, SpritePair]
    pillars: Tuple[SpritePair, SpritePair, SpritePair, SpritePair, SpritePair, SpritePair]
    flat: Tuple[SpritePair, SpritePair]
    ramp: Tuple[SpritePair, SpritePair]

    @staticmethod
    def one_grid_layout(back, front, pillars, flat, ramp):
        return SingleTypeBridgeLayout((back,) * 6, (front,) * 6, (pillars,) * 6, flat, ramp)


@dataclass
class BridgeLayout:
    rail: SingleTypeBridgeLayout
    road: SingleTypeBridgeLayout
    mono: SingleTypeBridgeLayout
    mlev: SingleTypeBridgeLayout

    @staticmethod
    def make_universal(single_layout):
        return BridgeLayout(rail=single_layout, road=single_layout, mono=single_layout, mlev=single_layout)


class Bridge(grf.SpriteGenerator):
    def __init__(self, *, id, name, layout: BridgeLayout, **props):
        super().__init__()
        self.id = id
        self.name = name
        self.layout = layout
        self._props = props

        # FIXME: supprt new layout abstraction
        self._props["layout"] = layout

    def get_sprites(self, g):
        extra_props = {}
        for prop in ("purchase_text", "description_rail", "description_road"):
            if prop in self._props:
                extra_props[prop] = g.strings.add(self._props[prop]).get_persistent_id()

        res = []

        if isinstance(self.name, grf.StringRef):
            name_action = self.name.get_actions(grf.BRIDGE, self.id)
        else:
            name_action = g.strings.add(self.name).get_actions(grf.BRIDGE, self.id)

        res.extend(name_action)
        res.append(grf.Define(feature=grf.BRIDGE, id=self.id, props={**self._props, **extra_props}))

        return res
