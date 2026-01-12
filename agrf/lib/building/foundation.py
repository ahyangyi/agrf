import grf
import json
import hashlib
from dataclasses import dataclass, replace
from dataclass_type_validator import dataclass_type_validator
from agrf.graphics import SCALE_TO_ZOOM
from agrf.graphics.sprites.foundation import FoundationSprite
from agrf.graphics.helpers.blend import blend_alternative_sprites
from agrf.magic import CachedFunctorMixin
from agrf.sprites.numbered import number_alternatives


@dataclass
class Foundation(CachedFunctorMixin):
    solid: grf.AlternativeSprites | None
    ground: grf.AlternativeSprites | None
    cut_inside: bool
    zshift: int = 0
    extended: bool = False
    nw_clip: bool = False
    ne_clip: bool = False
    sw_shareground: bool = False
    se_shareground: bool = False
    s_shareground: bool = False
    debug_number: int = -1

    def __post_init__(self):
        super().__init__()
        dataclass_type_validator(self)

    def fmap(self, f):
        g = lambda x: f(x) if x is not None else None
        return replace(self, solid=g(self.solid), ground=g(self.ground))

    def make_sprite(self, slope_type, render_context):
        foundations = self.make_foundations()

        if self.extended:
            if slope_type == 3:
                return foundations[0]
            elif slope_type == 5:
                return foundations[1]
            elif slope_type == 6:
                return foundations[2]
            elif slope_type == 7:
                return foundations[3]
            elif slope_type == 9:
                return foundations[4]
            elif slope_type == 10:
                return foundations[5]
            elif slope_type == 11:
                return foundations[6]
            elif slope_type == 12:
                return foundations[7]
            elif slope_type == 13:
                return foundations[8]
            elif slope_type == 14:
                return foundations[9]
            assert False, f"Unsupported slope_type: {slope_type}"
        else:
            if slope_type == 3:
                return foundations[5]
            elif slope_type == 5:
                return blend_alternative_sprites(foundations[0], foundations[3])
            elif slope_type == 6:
                return foundations[2]
            elif slope_type == 7:
                return blend_alternative_sprites(foundations[6], foundations[7])
            elif slope_type == 9:
                return blend_alternative_sprites(foundations[0], foundations[4])
            elif slope_type == 10:
                return blend_alternative_sprites(foundations[2], foundations[5])
            elif slope_type == 11:
                return blend_alternative_sprites(foundations[5], foundations[7])
            elif slope_type == 12:
                return blend_alternative_sprites(foundations[1], foundations[3])
            elif slope_type == 13:
                return blend_alternative_sprites(foundations[0], foundations[3])
            elif slope_type == 14:
                return blend_alternative_sprites(foundations[2])
            else:
                assert False, f"Unsupported slope_type: {slope_type}"

    def get_sprite_conf(self, style, i):
        left, right = {
            ("ground", 0): (7, 7),
            ("simple", 0): (6, None),
            ("simple", 1): (4, None),
            ("simple", 2): (5, None),
            ("simple", 3): (None, 6),
            ("simple", 4): (None, 4),
            ("simple", 5): (None, 5),
            ("simple", 6): (3, None),
            ("simple", 7): (None, 3),
            ("extended", 0): (3, 1),
            ("extended", 1): (2, 2),
            ("extended", 2): (1, 3),
            ("extended", 3): (3, 3),
            ("extended", 4): (6, 4),
            ("extended", 5): (5, 5),
            ("extended", 6): (7, 5),
            ("extended", 7): (4, 6),
            ("extended", 8): (6, 6),
            ("extended", 9): (5, 7),
        }[style, i]

        if left is not None:
            left = (left & 3) + (left & 6) * 2
            if self.nw_clip:
                left = left & 3
            if self.sw_shareground:
                left = left & 12

        if right is not None:
            right = (right & 3) + (right & 6) * 2
            if self.ne_clip:
                right = right & 3
            if self.se_shareground:
                right = right & 12

        return left, right

    def make_foundations_subset(self, subset):
        # sprite.voxel.render()  # FIXME agrf cannot correctly track dependencies here
        ret = []
        for style, i in subset:
            l, r = self.get_sprite_conf(style, i)
            alts = []
            for scale in [1, 2, 4]:
                for bpp in [32]:
                    if self.solid is not None:
                        s = self.solid.get_sprite(zoom=SCALE_TO_ZOOM[scale], bpp=bpp)
                    else:
                        s = None
                    if self.ground is not None:
                        g = self.ground.get_sprite(zoom=SCALE_TO_ZOOM[scale], bpp=bpp)
                    else:
                        g = None

                    if s is not None or g is not None:
                        fs = FoundationSprite(
                            s,
                            g,
                            l,
                            r,
                            self.s_shareground,
                            self.cut_inside,
                            zshift=self.zshift,
                            zoffset=(8 if style == "ground" else 0),
                        )
                        alts.append(fs)

            alt_sprite = grf.AlternativeSprites(*alts)
            if self.debug_number != -1:
                alt_sprite = number_alternatives(alt_sprite, self.debug_number)
            ret.append(alt_sprite)

        return ret

    def make_foundations(self):
        return self.make_foundations_subset(
            [("extended" if self.extended else "simple", i) for i in range(10 if self.extended else 8)]
        )

    def convert_foundation_to_ground(self):
        return self.make_foundations_subset([("ground", 0)])[0]

    def __hash__(self):
        return int.from_bytes(
            hashlib.sha384(json.dumps(self.get_fingerprint(), sort_keys=True).encode()).digest(), byteorder="big"
        )

    def get_fingerprint(self):
        return {
            "solid": self.solid.get_fingerprint() if self.solid is not None else None,
            "ground": self.ground.get_fingerprint() if self.ground is not None else None,
            "cut_inside": self.cut_inside,
            "zshift": self.zshift,
            "extended": int(self.extended),
            "nw_clip": int(self.nw_clip),
            "ne_clip": int(self.ne_clip),
            "sw_shareground": int(self.sw_shareground),
            "se_shareground": int(self.se_shareground),
            "s_shareground": int(self.s_shareground),
            "debug_number": self.debug_number,
        }
