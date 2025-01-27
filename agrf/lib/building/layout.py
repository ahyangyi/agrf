from dataclasses import dataclass, replace, field
from typing import List, Tuple
import grf
from PIL import Image
import functools
import numpy as np
from agrf.lib.building.symmetry import BuildingCylindrical, BuildingSymmetrical, BuildingRotational
from agrf.lib.building.registers import Registers
from agrf.graphics import LayeredImage, SCALE_TO_ZOOM
from agrf.graphics.spritesheet import LazyAlternativeSprites
from agrf.magic import CachedFunctorMixin, TaggedCachedFunctorMixin
from agrf.utils import unique_tuple
from agrf.pkg import load_third_party_image


@dataclass
class DefaultGraphics:
    sprite_id: int

    climate_dependent_tiles = {
        (climate, k): load_third_party_image(f"third_party/opengfx2/{climate}/{k}.png")
        for climate in ["temperate", "arctic", "tropical", "toyland"]
        for k in [1011, 1012, 1037, 1038, 3981, 4550]
    }
    climate_independent_tiles = {
        k: load_third_party_image(f"third_party/opengfx2/{k}.png") for k in [1313, 1314, 1320, 1321, 1322, 1323, 1420]
    }

    def graphics(self, scale, bpp, climate="temperate", subclimate="default"):
        # FIXME handle flags correctly
        if self.sprite_id in self.climate_independent_tiles:
            img = np.asarray(self.climate_independent_tiles[self.sprite_id])
        elif self.sprite_id == 3981:
            img = np.asarray(self.climate_dependent_tiles[(climate, 4550 if subclimate != "default" else 3981)])
        else:
            img = np.asarray(
                self.climate_dependent_tiles[(climate, self.sprite_id + (26 if subclimate != "default" else 0))]
            )
        ret = LayeredImage(-124, 0, 256, 127, img[:, :, :3], img[:, :, 3], None)
        if scale == 4:
            ret = ret.copy()
        elif scale == 2:
            ret.resize(128, 63)
        elif scale == 1:
            ret.resize(64, 31)
        return ret

    def to_spriteref(self, sprite_list):
        return grf.SpriteRef(
            id=self.sprite_id, pal=0, is_global=True, use_recolour=False, always_transparent=False, no_transparent=False
        )

    def to_action2_semidict(self, sprite_list):
        return {"sprite": grf.SpriteRef(self.sprite_id, is_global=True)}

    @property
    def sprites(self):
        return ()

    def get_fingerprint(self):
        return {"sprite_id": self.sprite_id}

    def get_resource_files(self):
        return ()


DEFAULT_GRAPHICS = {}
for x in [1420, 3872, 3981]:
    DEFAULT_GRAPHICS[x] = BuildingCylindrical.create_variants([DefaultGraphics(x)])
for x in [1011, 1313]:
    DEFAULT_GRAPHICS[x] = BuildingSymmetrical.create_variants([DefaultGraphics(x), DefaultGraphics(x + 1)])
    DEFAULT_GRAPHICS[x + 1] = DEFAULT_GRAPHICS[x].M
for x in [1320]:
    DEFAULT_GRAPHICS[x + 1] = BuildingRotational.create_variants(
        [DefaultGraphics(x + 1), DefaultGraphics(x), DefaultGraphics(x + 2), DefaultGraphics(x + 3)]
    )
    DEFAULT_GRAPHICS[x] = DEFAULT_GRAPHICS[x + 1].R
    DEFAULT_GRAPHICS[x + 2] = DEFAULT_GRAPHICS[x + 1].T
    DEFAULT_GRAPHICS[x + 3] = DEFAULT_GRAPHICS[x + 1].T.R


@dataclass
class NewGraphics(CachedFunctorMixin):
    sprite: grf.ResourceAction
    recolour: bool = True
    palette: int = 0

    def __post_init__(self):
        super().__init__()
        assert (
            self.sprite is grf.EMPTY_SPRITE or callable(self.sprite) or isinstance(self.sprite, grf.ResourceAction)
        ), type(self.sprite)

    def graphics(self, scale, bpp, climate="temperate", subclimate="default"):
        if self.sprite is grf.EMPTY_SPRITE:
            return LayeredImage.empty()
        ret = None
        sprite = self.sprite.get_sprite(zoom=SCALE_TO_ZOOM[scale], bpp=bpp)
        if sprite is not None:
            ret = LayeredImage.from_sprite(sprite).copy()

        if ret is None and bpp == 32:
            # Fall back to bpp=8
            sprite = self.sprite.get_sprite(zoom=SCALE_TO_ZOOM[scale], bpp=8)
            ret = LayeredImage.from_sprite(sprite).copy().to_rgb()
        assert ret is not None

        return ret

    def to_spriteref(self, sprite_list):
        return grf.SpriteRef(
            id=0x42D + sprite_list.index(self.sprite),
            pal=self.palette,
            is_global=False,
            use_recolour=self.recolour,
            always_transparent=False,
            no_transparent=False,
        )

    def to_action2_semidict(self, sprite_list):
        return {"sprite": grf.SpriteRef(sprite_list.index(self.sprite), is_global=False)}

    @property
    def sprites(self):
        return (self.sprite,)

    def fmap(self, f):
        return replace(self, sprite=self.sprite if self.sprite is grf.EMPTY_SPRITE else f(self.sprite))

    def get_fingerprint(self):
        if isinstance(self.sprite, LazyAlternativeSprites):
            fingerprint = self.sprite.get_fingerprint()
        else:
            fingerprint = id(self.sprite)
        return {"sprite": fingerprint}

    def get_resource_files(self):
        return ()

    @property
    def symmetry(self):
        return self.sprite.symmetry


@dataclass
class GroundPosition:
    @property
    def T(self):
        return self

    R = M = T

    def to_parentsprite(self, low=False):
        height = 0 if low else 1
        return BBoxPosition(extent=(16, 16, height), offset=(0, 0, 0))

    def pushdown(self, steps):
        return self.to_parentsprite().pushdown(steps)

    def get_fingerprint(self):
        return {"position": "ground"}

    def to_action2_semidict(self, sprite_list):
        return {}


@dataclass
class BBoxPosition:
    extent: Tuple[int, int, int]
    offset: Tuple[int, int, int]

    @property
    def T(self):
        new_offset = (self.offset[0], 16 - self.offset[1] - self.extent[1], self.offset[2])
        return BBoxPosition(self.extent, new_offset)

    @property
    def R(self):
        new_offset = (16 - self.offset[0] - self.extent[0], self.offset[1], self.offset[2])
        return BBoxPosition(self.extent, new_offset)

    @staticmethod
    def _mirror(triplet):
        return triplet[1], triplet[0], triplet[2]

    @property
    def M(self):
        return BBoxPosition(BBoxPosition._mirror(self.extent), BBoxPosition._mirror(self.offset))

    def pushdown(self, steps):
        x, y, z = self.offset
        for i in range(steps):
            if z >= 2:
                z -= 2
            else:
                x += 1
                y += 1
        return BBoxPosition(self.extent, (x, y, z))

    def move(self, xofs, yofs):
        return replace(self, offset=(self.offset[0] + xofs, self.offset[1] + yofs, self.offset[2]))

    def up(self, zdiff):
        new_offset = (self.offset[0], self.offset[1], self.offset[2] + zdiff)
        return replace(self, offset=new_offset)

    def get_fingerprint(self):
        return {"extent": self.extent, "offset": self.offset}

    def to_action2_semidict(self, sprite_list):
        return {"extent": self.extent, "offset": self.offset}

    def demo_translate(self, xofs, yofs, zofs):
        return replace(self, offset=(self.offset[0] + xofs, self.offset[1] + yofs, self.offset[2] + zofs * 8))


@dataclass
class OffsetPosition:
    offset: Tuple[int, int]

    @property
    def T(self):
        return self

    R = M = T

    def get_fingerprint(self):
        return {"pixel_offset": self.offset}

    def to_action2_semidict(self, sprite_list):
        return {"pixel_offset": self.offset}


@dataclass
class NewGeneralSprite(TaggedCachedFunctorMixin):
    sprite: DefaultGraphics | NewGraphics
    position: GroundPosition | BBoxPosition | OffsetPosition
    child_sprites: list = field(default_factory=list)
    flags: dict = field(default_factory=dict)

    def __post_init__(self):
        super().__init__()
        if self.child_sprites is None:
            self.child_sprites = []
        if self.flags is None:
            self.flags = {}
        if self.is_childsprite():
            assert len(self.child_sprites) == 0

    def is_childsprite(self):
        return isinstance(self.position, OffsetPosition)

    def __repr__(self):
        return f"<GeneralSprite:{self.sprite}:{self.position}:{self.child_sprites}:{self.flags}>"

    @property
    def sprites(self):
        return unique_tuple(self.sprite.sprites + tuple(s for c in self.child_sprites for s in c.sprites))

    def fmap(self, f, method_name):
        if method_name in ["T", "R", "M"]:
            return replace(
                self, sprite=f(self.sprite), position=f(self.position), child_sprites=[f(c) for c in self.child_sprites]
            )
        if method_name in ["move", "demo_translate", "up"]:
            return replace(self, position=f(self.position))
        return replace(self, sprite=f(self.sprite), child_sprites=[f(c) for c in self.child_sprites])

    def graphics(self, scale, bpp, climate="temperate", subclimate="default"):
        if self.flags.get("dodraw") == Registers.SNOW and subclimate != "snow":
            return LayeredImage.empty()
        if self.flags.get("dodraw") == Registers.NOSNOW and subclimate == "snow":
            return LayeredImage.empty()

        ret = self.sprite.graphics(scale, bpp, climate=climate, subclimate=subclimate)

        for c in self.child_sprites:
            masked_sprite = c.graphics(scale, bpp, climate=climate, subclimate=subclimate)
            ret.blend_over(masked_sprite, childsprite=isinstance(self.position, BBoxPosition))

        return ret

    def to_parentsprite(self, low=False):
        height = 0 if low else 1
        assert isinstance(self.position, GroundPosition)
        return replace(self, position=BBoxPosition(extent=(16, 16, height), offset=(0, 0, 0)))

    def pushdown(self, steps):
        return replace(self, position=self.position.pushdown(steps))

    def __add__(self, child_sprite):
        if child_sprite is None:
            return self
        return replace(self, child_sprites=self.child_sprites + [child_sprite])

    def filter_register(self, reg):
        return replace(self, child_sprites=[x for x in self.child_sprites if x.flags.get("dodraw") != reg])

    @property
    def offset(self):
        assert isinstance(self.position, BBoxPosition)
        return self.position.offset

    @property
    def extent(self):
        assert isinstance(self.position, BBoxPosition)
        return self.position.extent

    @property
    def flags_translated(self):
        return {k: (v if k == "add" else v.get_index()) for k, v in self.flags.items() if v is not None}

    def registers_to_grf_dict(self):
        return {"flags": sum(grf.SPRITE_FLAGS[k][1] for k in self.flags.keys()), "registers": self.flags_translated}

    def to_grf(self, sprite_list):
        if isinstance(self.position, OffsetPosition):
            return [
                grf.ChildSprite(
                    sprite=self.sprite.to_spriteref(sprite_list),
                    xofs=self.position.offset[0],
                    yofs=self.position.offset[1],
                    **self.registers_to_grf_dict(),
                )
            ]
        if isinstance(self.position, GroundPosition):
            ps = grf.GroundSprite(sprite=self.sprite.to_spriteref(sprite_list), **self.registers_to_grf_dict())
        else:
            ps = grf.ParentSprite(
                sprite=self.sprite.to_spriteref(sprite_list),
                extent=self.position.extent,
                offset=self.position.offset,
                **self.registers_to_grf_dict(),
            )
        return [ps] + [grfobj for child_sprite in self.child_sprites for grfobj in child_sprite.to_grf(sprite_list)]

    def to_action2(self, sprite_list):
        return [{**self.sprite.to_action2_semidict(sprite_list), **self.position.to_action2_semidict(sprite_list)}] + [
            s for x in self.child_sprites for s in x.to_action2(sprite_list)
        ]

    def get_fingerprint(self):
        return {
            "sprite": self.sprite.get_fingerprint(),
            "position": self.position.get_fingerprint(),
            "child_sprites": [c.get_fingerprint() for c in self.child_sprites],
        }

    def get_resource_files(self):
        return unique_tuple(f for x in [self.sprite] + self.child_sprites for f in x.get_resource_files())


def ADefaultGroundSprite(sprite, flags=None):
    return NewGeneralSprite(sprite=DEFAULT_GRAPHICS[sprite], position=GroundPosition(), child_sprites=[], flags=flags)


def AGroundSprite(sprite, flags=None):
    return NewGeneralSprite(sprite=NewGraphics(sprite), position=GroundPosition(), child_sprites=[], flags=flags)


def ADefaultParentSprite(sprite, extent, offset, child_sprites=None, flags=None):
    return NewGeneralSprite(
        sprite=DEFAULT_GRAPHICS[sprite],
        position=BBoxPosition(extent=extent, offset=offset),
        child_sprites=child_sprites,
        flags=flags,
    )


def AParentSprite(sprite, extent, offset, child_sprites=None, flags=None, recolour=True, palette=0):
    return NewGeneralSprite(
        sprite=NewGraphics(sprite, recolour=recolour, palette=palette),
        position=BBoxPosition(extent=extent, offset=offset),
        child_sprites=child_sprites,
        flags=flags,
    )


def AChildSprite(sprite, offset, flags=None, recolour=True, palette=0):
    return NewGeneralSprite(
        sprite=NewGraphics(sprite, recolour=recolour, palette=palette),
        position=OffsetPosition(offset=offset),
        flags=flags,
    )


def overlaps(a0, a1, b0, b1):
    assert a0 <= a1 and b0 <= b1
    return a1 > b0 and b1 > a0


def is_in_front(a, b):
    ax0, ay0, az0 = a.offset
    ax1, ay1, az1 = (x + y for x, y in zip(a.offset, a.extent))
    bx0, by0, bz0 = b.offset
    bx1, by1, bz1 = (x + y for x, y in zip(b.offset, b.extent))
    if not overlaps(ax0 - az1, ax1 - az0, bx0 - bz1, bx1 - bz0):
        return False
    if not overlaps(ay0 - az1, ay1 - az0, by0 - bz1, by1 - bz0):
        return False
    if not overlaps(ax0 - ay1, ax1 - ay0, bx0 - by1, bx1 - by0):
        return False
    if ax0 >= bx1:
        return True
    if ay0 >= by1:
        return True
    if az0 >= bz1:
        return True
    return False


@dataclass(eq=False)
class ALayout:
    ground_sprite: object
    parent_sprites: list
    traversable: bool
    category: str = None
    notes: list = None
    flattened: bool = False
    altitude: int = 0

    def __post_init__(self):
        from agrf.lib.building.default import empty_ground

        if self.ground_sprite is None:
            self.ground_sprite = empty_ground
        assert isinstance(self.ground_sprite, NewGeneralSprite)
        assert all(isinstance(s, NewGeneralSprite) for s in self.parent_sprites), [type(s) for s in self.parent_sprites]
        self.notes = self.notes or []

    @property
    def sorted_parent_sprites(self):
        if self.flattened:
            return self.parent_sprites
        for i in self.parent_sprites:
            for j in self.parent_sprites:
                if i != j:
                    assert not all(
                        i.offset[k] + i.extent[k] > j.offset[k] and j.offset[k] + j.extent[k] > i.offset[k]
                        for k in range(3)
                    ), f"{i} and {j} overlap\nSprites: {self.parent_sprites}"

        ret = []
        for i in range(len(self.parent_sprites)):
            for j in self.parent_sprites:
                if j in ret:
                    continue
                good = True
                for k in self.parent_sprites:
                    if k != j and k not in ret and is_in_front(j, k):
                        good = False
                        break
                if good:
                    ret.append(j)
                    break
            assert len(ret) == i + 1, f"{self.parent_sprites}, {i}, {ret}"
        return ret

    def pushdown(self, steps):
        from agrf.lib.building.default import empty_ground

        return ALayout(
            empty_ground,
            [s.pushdown(steps) for s in [self.ground_sprite.to_parentsprite()] + self.sorted_parent_sprites],
            self.traversable,
            category=self.category,
            notes=self.notes,
            flattened=True,
            altitude=self.altitude,
        )

    @functools.cache
    def squash(self, ratio):
        return replace(self, parent_sprites=[s.squash(ratio) for s in self.sorted_parent_sprites])

    @functools.cache
    def raise_tile(self, delta=1):
        return replace(self, altitude=self.altitude + delta)

    @functools.cache
    def lower_tile(self, delta=1):
        return self.raise_tile(-delta)

    @functools.cache
    def filter_register(self, reg):
        return replace(
            self,
            ground_sprite=self.ground_sprite.filter_register(reg),
            parent_sprites=[s.filter_register(reg) for s in self.parent_sprites if s.flags.get("dodraw") != reg],
        )

    @functools.cache
    def demo_translate(self, xofs, yofs):
        from agrf.lib.building.default import empty_ground

        return replace(
            self,
            ground_sprite=empty_ground,
            parent_sprites=[
                s.demo_translate(xofs, yofs, self.altitude)
                for s in [self.ground_sprite.to_parentsprite(low=True)] + self.sorted_parent_sprites
            ],
            altitude=0,
        )

    def to_grf(self, sprite_list):
        if self.flattened:
            parent_sprites = self.parent_sprites
        else:
            parent_sprites = self.sorted_parent_sprites
        return grf.SpriteLayout(
            [s for s in self.ground_sprite.to_grf(sprite_list)]
            + [s for sprite in parent_sprites for s in sprite.to_grf(sprite_list)]
        )

    def to_action2(self, feature, sprite_list):
        ground = self.ground_sprite.to_action2(sprite_list)
        buildings = [s for sprite in self.sorted_parent_sprites for s in sprite.to_action2(sprite_list)]
        return grf.AdvancedSpriteLayout(ground=ground[0], feature=feature, buildings=tuple(ground[1:] + buildings))

    def graphics(self, scale, bpp, remap=None, context=None, climate="temperate", subclimate="default"):
        context = context or grf.DummyWriteContext()
        img = LayeredImage.empty()

        new_img = self.ground_sprite.graphics(scale, bpp, climate=climate, subclimate=subclimate).copy()
        img.blend_over(new_img)

        for sprite in self.sorted_parent_sprites:
            masked_sprite = sprite.graphics(scale, bpp, climate=climate, subclimate=subclimate)
            if remap is not None:
                masked_sprite.remap(remap)
                masked_sprite.apply_mask()

            img.blend_over(
                masked_sprite.move(
                    (-sprite.offset[0] * 2 + sprite.offset[1] * 2) * scale,
                    (sprite.offset[0] + sprite.offset[1] - sprite.offset[2]) * scale,
                )
            )

        return img.move(0, -self.altitude * 8 * scale)

    def to_index(self, layout_pool):
        return layout_pool.index(self)

    def __repr__(self):
        return f"<ALayout:{self.ground_sprite}:{self.parent_sprites}>"

    def __getattr__(self, name):
        call = lambda x: getattr(x, name)
        new_ground_sprite = call(self.ground_sprite)
        new_sprites = [call(sprite) for sprite in self.parent_sprites]
        return ALayout(
            new_ground_sprite, new_sprites, self.traversable, self.category, self.notes, altitude=self.altitude
        )

    def __call__(self, *args, **kwargs):
        call = lambda x: x(*args, **kwargs)
        new_ground_sprite = call(self.ground_sprite)
        new_sprites = [call(sprite) for sprite in self.parent_sprites]
        return ALayout(
            new_ground_sprite, new_sprites, self.traversable, self.category, self.notes, altitude=self.altitude
        )

    @property
    def sprites(self):
        return list(dict.fromkeys([sub for s in [self.ground_sprite] + self.parent_sprites for sub in s.sprites]))

    def get_fingerprint(self):
        return {
            "ground_sprite": self.ground_sprite.get_fingerprint(),
            "parent_sprites": [s.get_fingerprint() for s in self.parent_sprites],
        }

    def get_resource_files(self):
        return unique_tuple(f for x in [self.ground_sprite] + self.parent_sprites for f in x.get_resource_files())


class LayoutSprite(grf.Sprite):
    def __init__(self, layout, w, h, scale, bpp, **kwargs):
        super().__init__(w, h, zoom=SCALE_TO_ZOOM[scale], **kwargs)
        self.layout = layout
        self.scale = scale
        self.bpp = bpp

    def get_fingerprint(self):
        return {
            "layout": self.layout.get_fingerprint(),
            "w": self.w,
            "h": self.h,
            "bpp": self.bpp,
            "xofs": self.xofs,
            "yofs": self.yofs,
        }

    def get_resource_files(self):
        return self.layout.get_resource_files()

    def get_data_layers(self, context):
        timer = context.start_timer()
        ret = self.layout.graphics(self.scale, self.bpp)
        ret.resize(self.w, self.h)
        timer.count_composing()

        self.xofs += ret.xofs
        self.yofs += ret.yofs

        return ret.w, ret.h, ret.rgb, ret.alpha, ret.mask
