import grf
import json
import hashlib
from dataclasses import dataclass, replace
from dataclass_type_validator import dataclass_type_validator
from agrf.graphics import SCALE_TO_ZOOM
from agrf.graphics.sprites.foundation import FoundationSprite
from agrf.graphics.helpers.blend import blend_alternative_sprites
from agrf.magic import CachedFunctorMixin


@dataclass
class Foundation(CachedFunctorMixin):
    solid: grf.AlternativeSprites | None
    ground: grf.AlternativeSprites | None
    cut_inside: bool
    zshift: int = 0

    def __post_init__(self):
        super().__init__()
        dataclass_type_validator(self)

    def fmap(self, f):
        g = lambda x: f(x) if x is not None else None
        return replace(self, solid=g(self.solid), ground=g(self.ground))

    def make_sprite(self, slope_type):
        foundations = self.make_foundations()

        if slope_type == 3:
            return foundations[5]
        elif slope_type == 6:
            return foundations[2]
        elif slope_type == 9:
            return blend_alternative_sprites(foundations[0], foundations[4])
        elif slope_type == 12:
            return blend_alternative_sprites(foundations[1], foundations[3])
        elif slope_type == 8:
            return blend_alternative_sprites(foundations[1], foundations[4])
        else:
            assert False, f"Unsupported slope_type: {slope_type}"

    def make_foundations_subset(self, subset):
        # sprite.voxel.render()  # FIXME agrf cannot correctly track dependencies here
        ret = []
        for i in subset:
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
                        fs = FoundationSprite(s, g, i, self.cut_inside, zshift=self.zshift)
                        alts.append(fs)

            ret.append(grf.AlternativeSprites(*alts))
        return ret

    def make_foundations(self):
        return self.make_foundations_subset(range(8))

    def convert_foundation_to_ground(self):
        return self.make_foundations_subset([8])[0]

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
        }
