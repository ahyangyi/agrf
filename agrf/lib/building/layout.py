from dataclasses import dataclass, replace, field
from typing import List, Tuple, Callable
from dataclass_type_validator import dataclass_type_validator
import grf
from PIL import Image
import functools
import numpy as np
from .symmetry import (
    BuildingCylindrical,
    BuildingSymmetrical,
    BuildingSymmetricalX,
    BuildingSymmetricalY,
    BuildingDiagonal,
)
from .registers import Registers
from agrf.graphics import LayeredImage, SCALE_TO_ZOOM, ZOOM_TO_SCALE
from agrf.graphics.spritesheet import LazyAlternativeSprites
from agrf.magic import CachedFunctorMixin, TaggedCachedFunctorMixin
from agrf.utils import unique, unique_tuple
from agrf.pkg import load_third_party_image


@dataclass(frozen=True)
class RenderContext:
    climate: str = None
    subclimate: str = None
    rail_type: str = None

    def dodraw(self, register):
        return True


DEFAULT_RENDER_CONTEXT = RenderContext(climate="temperate", subclimate="default", rail_type="default")


@dataclass
class DefaultGraphics:
    sprite_id: int
    yofs: int = 0

    climate_dependent_tiles = {}
    climate_independent_tiles = {}

    @staticmethod
    def register_third_party_image(img_path, climate, sprite_id):
        DefaultGraphics.climate_dependent_tiles[(climate, sprite_id)] = Image.open(img_path)

    def graphics(self, scale, bpp, render_context: RenderContext = DEFAULT_RENDER_CONTEXT):
        if 3981 <= self.sprite_id <= 4012 and render_context.subclimate != "default":
            sprite_id_to_load = self.sprite_id + 569
        elif self.sprite_id in [1011, 1012] and render_context.subclimate != "default":
            sprite_id_to_load = self.sprite_id + 26
        elif self.sprite_id in [1332, 1333] and render_context.subclimate != "default":
            sprite_id_to_load = self.sprite_id + 19
        else:
            sprite_id_to_load = self.sprite_id

        if self.sprite_id in [1011, 1012] and render_context.rail_type == "monorail":
            sprite_id_to_load += 82
        elif self.sprite_id in [1011, 1012] and render_context.rail_type == "maglev":
            sprite_id_to_load += 164

        if (render_context.climate, sprite_id_to_load) in DefaultGraphics.climate_dependent_tiles:
            img = DefaultGraphics.climate_dependent_tiles[(render_context.climate, sprite_id_to_load)]
        elif render_context.climate in DefaultGraphics.climate_independent_tiles:
            img = DefaultGraphics.climate_independent_tiles[sprite_id_to_load]
        else:
            try:
                img = load_third_party_image(f"third_party/opengfx2/{render_context.climate}/{sprite_id_to_load}.png")
                DefaultGraphics.climate_dependent_tiles[(render_context.climate, sprite_id_to_load)] = img
            except:
                img = load_third_party_image(f"third_party/opengfx2/{sprite_id_to_load}.png")
                DefaultGraphics.climate_independent_tiles[sprite_id_to_load] = img

        img = np.asarray(img)
        h = img.shape[0]
        ret = LayeredImage(-124, 127 + self.yofs * 4 - h, 256, h, img[:, :, :3], img[:, :, 3], None)
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
for x in [66, 72]:
    DEFAULT_GRAPHICS[x] = BuildingCylindrical.create_variants([DefaultGraphics(x, yofs=-8)])
for x in [1420, 3872, 3981]:
    DEFAULT_GRAPHICS[x] = BuildingCylindrical.create_variants([DefaultGraphics(x)])
for x in [1011, 1093, 1175, 1313, 1332]:
    DEFAULT_GRAPHICS[x] = BuildingSymmetrical.create_variants([DefaultGraphics(x), DefaultGraphics(x + 1)])
    DEFAULT_GRAPHICS[x + 1] = DEFAULT_GRAPHICS[x].M

DEFAULT_GRAPHICS[1031] = BuildingSymmetricalY.create_variants(
    [DefaultGraphics(1031), DefaultGraphics(1034), DefaultGraphics(1033, yofs=-8), DefaultGraphics(1032, yofs=-8)]
)
DEFAULT_GRAPHICS[1032] = DEFAULT_GRAPHICS[1031].R.M
DEFAULT_GRAPHICS[1033] = DEFAULT_GRAPHICS[1031].R
DEFAULT_GRAPHICS[1034] = DEFAULT_GRAPHICS[1031].M

# FIXME: only some entries are correct
DEFAULT_GRAPHICS[3992] = BuildingDiagonal.create_variants(
    [DefaultGraphics(3992), DefaultGraphics(3994), DefaultGraphics(3996), DefaultGraphics(3995)]
)
DEFAULT_GRAPHICS[3994] = DEFAULT_GRAPHICS[3992].R

DEFAULT_GRAPHICS[3989] = BuildingDiagonal.create_variants(
    [DefaultGraphics(3989), DefaultGraphics(3982), DefaultGraphics(3983), DefaultGraphics(3984)]
)
DEFAULT_GRAPHICS[3982] = DEFAULT_GRAPHICS[3989].R

DEFAULT_GRAPHICS[3990] = BuildingSymmetricalX.create_variants(
    [DefaultGraphics(3990), DefaultGraphics(3993), DefaultGraphics(3987, yofs=-24), DefaultGraphics(3984, yofs=-24)]
)

for x in [1320]:
    DEFAULT_GRAPHICS[x + 1] = BuildingDiagonal.create_variants(
        [DefaultGraphics(x + 1), DefaultGraphics(x), DefaultGraphics(x + 2), DefaultGraphics(x + 3)]
    )
    DEFAULT_GRAPHICS[x] = DEFAULT_GRAPHICS[x + 1].R
    DEFAULT_GRAPHICS[x + 2] = DEFAULT_GRAPHICS[x + 1].T
    DEFAULT_GRAPHICS[x + 3] = DEFAULT_GRAPHICS[x + 1].T.R


@dataclass
class NewGraphics(CachedFunctorMixin):
    sprite: grf.Sprite | grf.AlternativeSprites | grf.ResourceAction | Callable
    recolour: bool = True
    palette: int = 0

    def __post_init__(self):
        super().__init__()
        dataclass_type_validator(self)

    def best_fit_sprite(self, scale, bpp):
        if self.sprite is grf.EMPTY_SPRITE:
            return None
        best_fit = None
        for sprite in self.sprite.sprites:
            fit_score = 0
            if sprite.bpp != bpp:
                fit_score -= 1
            if ZOOM_TO_SCALE[sprite.zoom] < scale:
                fit_score -= scale // ZOOM_TO_SCALE[sprite.zoom] * 256
            elif ZOOM_TO_SCALE[sprite.zoom] > scale:
                fit_score -= ZOOM_TO_SCALE[sprite.zoom] // scale * 2
            if best_fit is None or fit_score > best_fit_score:
                best_fit = sprite
                best_fit_score = fit_score

        assert best_fit is not None
        return best_fit

    def estimate_offset(self, scale):
        best_fit = self.best_fit_sprite(scale, 32)
        at_scale = ZOOM_TO_SCALE[best_fit.zoom]
        return best_fit.xofs * scale // at_scale, best_fit.yofs * scale // at_scale, best_fit.crop

    def graphics(self, scale, bpp, render_context: RenderContext = DEFAULT_RENDER_CONTEXT):
        if self.sprite is grf.EMPTY_SPRITE:
            return LayeredImage.empty()

        best_fit = self.best_fit_sprite(scale, bpp)

        ret = LayeredImage.from_sprite(best_fit).copy()
        if bpp == 32 and best_fit.bpp == 8:
            ret = ret.to_rgb()
        if best_fit.zoom != SCALE_TO_ZOOM[scale]:
            w, h = ret.w, ret.h
            new_w, new_h = int(ret.w * scale // ZOOM_TO_SCALE[best_fit.zoom]), int(
                ret.h * scale // ZOOM_TO_SCALE[best_fit.zoom]
            )
            ret.resize(new_w, new_h, force_nearest=True)

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
        return BBoxPosition(extent=(16, 16, height), offset=(0, 0, 0), is_ground=True)

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
    is_ground: bool = False

    @property
    def T(self):
        new_offset = (self.offset[0], 16 - self.offset[1] - self.extent[1], self.offset[2])
        return replace(self, extent=self.extent, offset=new_offset)

    @property
    def R(self):
        new_offset = (16 - self.offset[0] - self.extent[0], self.offset[1], self.offset[2])
        return replace(self, extent=self.extent, offset=new_offset)

    @staticmethod
    def _mirror(triplet):
        return triplet[1], triplet[0], triplet[2]

    @property
    def M(self):
        return replace(self, extent=BBoxPosition._mirror(self.extent), offset=BBoxPosition._mirror(self.offset))

    def pushdown(self, steps):
        x, y, z = self.offset
        for i in range(steps):
            if z >= 2:
                z -= 2
            else:
                x += 1
                y += 1
        return replace(self, extent=self.extent, offset=(x, y, z))

    def move(self, xofs, yofs, zofs=0):
        return replace(self, offset=(self.offset[0] + xofs, self.offset[1] + yofs, self.offset[2] + zofs))

    def up(self, zdiff):
        return self.move(0, 0, zofs=zdiff)

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

    extra_sprites: dict = None

    def __post_init__(self):
        super().__init__()
        if self.child_sprites is None:
            self.child_sprites = []
        if self.flags is None:
            self.flags = {}
        if self.is_childsprite():
            assert len(self.child_sprites) == 0
        if self.extra_sprites is None:
            self.extra_sprites = {}
        else:
            self.extra_sprites = self.extra_sprites.copy()
        dataclass_type_validator(self)

    def is_childsprite(self):
        return isinstance(self.position, OffsetPosition)

    def __repr__(self):
        return f"<GeneralSprite:{self.sprite}:{self.position}:{self.child_sprites}:{self.flags}>"

    def copy(self):
        return replace(self)

    @property
    def sprites(self):
        return unique_tuple(self.sprite.sprites + tuple(s for c in self.child_sprites for s in c.sprites))

    def fmap(self, f, method_name):
        if method_name in ["T", "R", "M"]:
            return replace(
                self,
                sprite=f(self.sprite),
                position=f(self.position),
                child_sprites=[f(c) for c in self.child_sprites],
                extra_sprites={k: f(v) for k, v in self.extra_sprites.items()},
            )
        if method_name in ["move", "demo_translate", "up"]:
            return replace(self, position=f(self.position))
        return replace(self, sprite=f(self.sprite), child_sprites=[f(c) for c in self.child_sprites])

    @staticmethod
    def get_parentsprite_offset(g, scale):
        if isinstance(g, NewGraphics):
            s = g.sprite
            if isinstance(s, grf.AlternativeSprites):
                ofs = g.estimate_offset(scale)

                assert not ofs[2] or isinstance(s, LazyAlternativeSprites) and "agrf_manual_crop" in s.voxel.config, s

                return ofs[0], ofs[1]

        raise NotImplementedError(g)

    @staticmethod
    def get_childsprite_offset(g, scale):
        if isinstance(g, NewGraphics):
            s = g.sprite
            if isinstance(s, LazyAlternativeSprites):
                cfg = s.voxel.config
                cs = cfg.get("agrf_childsprite", (0, 0))

                return cs[0] * scale, cs[1] * scale
            elif isinstance(s, grf.AlternativeSprites):
                return 0, 0

        raise NotImplementedError(g)

    def graphics(self, scale, bpp, remap=None, render_context: RenderContext = DEFAULT_RENDER_CONTEXT):
        if self.flags.get("dodraw") == Registers.SNOW and render_context.subclimate != "snow":
            return LayeredImage.empty()
        if self.flags.get("dodraw") == Registers.NOSNOW and render_context.subclimate == "snow":
            return LayeredImage.empty()
        if self.flags.get("dodraw") == Registers.NOSLOPE:
            return LayeredImage.empty()
        if "dodraw" in self.flags and not render_context.dodraw(self.flags["dodraw"]):
            return LayeredImage.empty()

        ret = self.sprite.graphics(scale, bpp, render_context=render_context)

        for c in self.child_sprites:
            masked_sprite = c.graphics(scale, bpp, render_context=render_context)
            if remap is not None:
                masked_sprite.remap(remap)
                masked_sprite.apply_mask()

            parentsprite_offset = NewGeneralSprite.get_parentsprite_offset(self.sprite, scale)
            childsprite_offset = NewGeneralSprite.get_childsprite_offset(c.sprite, scale)

            masked_sprite.move(
                parentsprite_offset[0] - childsprite_offset[0], parentsprite_offset[1] - childsprite_offset[1]
            )

            ret.blend_over(masked_sprite)

        return ret

    def to_parentsprite(self, low=False):
        height = 0 if low else 1
        assert isinstance(self.position, GroundPosition)
        return replace(self, position=BBoxPosition(extent=(16, 16, height), offset=(0, 0, 0), is_ground=True))

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

    def is_empty(self):
        return isinstance(self.sprite, NewGraphics) and self.sprite.sprite is grf.EMPTY_SPRITE

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
        return [
            {
                **self.sprite.to_action2_semidict(sprite_list),
                **self.position.to_action2_semidict(sprite_list),
                **self.flags_translated,
            }
        ] + [s for x in self.child_sprites for s in x.to_action2(sprite_list)]

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
    if not overlaps(ax0 * 2 - az1, ax1 * 2 - az0, bx0 * 2 - bz1, bx1 * 2 - bz0):
        return False
    if not overlaps(ay0 * 2 - az1, ay1 * 2 - az0, by0 * 2 - bz1, by1 * 2 - bz0):
        return False
    if not overlaps(ax0 - ay1, ax1 - ay0, bx0 - by1, bx1 - by0):
        return False
    if ax0 >= bx1:
        return True
    if ay0 >= by1:
        return True
    # Special case: we don't sort zero height sprites
    if az0 == bz0 == az1 == bz1 and (a.position.is_ground ^ b.position.is_ground):
        return b.position.is_ground and not a.position.is_ground

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
    foundation: object = None
    purchase: object = None

    def __post_init__(self):
        from agrf.lib.building.default import empty_ground

        if self.ground_sprite is None:
            self.ground_sprite = empty_ground
        assert isinstance(self.ground_sprite, NewGeneralSprite), self.ground_sprite
        assert all(isinstance(s, NewGeneralSprite) for s in self.parent_sprites), [type(s) for s in self.parent_sprites]
        self.notes = self.notes or []

    @property
    def sorted_parent_sprites(self):
        if self.flattened:
            return self.parent_sprites

        sprites = [x for x in self.parent_sprites if not x.is_empty()]

        for i in sprites:
            for j in sprites:
                if i != j:
                    assert not all(
                        i.offset[k] + i.extent[k] > j.offset[k] and j.offset[k] + j.extent[k] > i.offset[k]
                        for k in range(3)
                    ), f"{i} and {j} overlap\nSprites: {sprites}"

        ret = []
        for i in range(len(sprites)):
            for j in sprites:
                if j in ret:
                    continue
                good = True
                for k in sprites:
                    if k != j and k not in ret and is_in_front(j, k):
                        good = False
                        break
                if good:
                    ret.append(j)
                    break
            assert len(ret) == i + 1, f"Some sprites cannot be sorted: {[x for x in sprites if x not in ret]}"

        return ret

    def copy(self):
        return replace(self)

    def pushdown(self, steps, flatten=True, low=False):
        from agrf.lib.building.default import empty_ground

        return replace(
            self,
            ground_sprite=empty_ground,
            parent_sprites=[
                s.pushdown(steps) for s in [self.ground_sprite.to_parentsprite(low=low)] + self.sorted_parent_sprites
            ],
            flattened=flatten,
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

    @functools.cache
    def demo_filter(self, render_context=DEFAULT_RENDER_CONTEXT):
        return self

    def add_foundation(self, foundation_obj, slope_type):
        sp = foundation_obj.make_sprite(slope_type)
        return replace(
            self, parent_sprites=self.parent_sprites + [AParentSprite(sp, (16, 16, 0), (0, 0, -8))]
        ).pushdown(0, low=True, flatten=False)

    def add_default_foundation(self, foundation_id):
        return replace(
            self, parent_sprites=self.parent_sprites + [ADefaultParentSprite(foundation_id, (16, 16, 0), (0, 0, -8))]
        ).pushdown(0, low=True, flatten=False)

    def enable_foundation(self, slope_type):
        if self.foundation is not None:
            return self.add_foundation(self.foundation, slope_type)

        raise NotImplementedError()

    def to_grf(self, sprite_list):
        if self.flattened:
            parent_sprites = self.parent_sprites
        else:
            parent_sprites = self.sorted_parent_sprites

        ret = [s for sprite in [self.ground_sprite] + parent_sprites for s in sprite.to_grf(sprite_list)]
        assert len(ret) < 64
        return grf.SpriteLayout(ret)

    def to_action2(self, feature, sprite_list):
        ground = self.ground_sprite.to_action2(sprite_list)
        buildings = [s for sprite in self.sorted_parent_sprites for s in sprite.to_action2(sprite_list)]
        return grf.AdvancedSpriteLayout(ground=ground[0], feature=feature, buildings=tuple(ground[1:] + buildings))

    def graphics(self, scale, bpp, remap=None, context=None, render_context: RenderContext = DEFAULT_RENDER_CONTEXT):
        context = context or grf.DummyWriteContext()
        img = LayeredImage.empty()

        new_img = self.ground_sprite.graphics(scale, bpp, render_context=render_context).copy()
        img.blend_over(new_img)

        for sprite in self.sorted_parent_sprites:
            masked_sprite = sprite.graphics(scale, bpp, remap=remap, render_context=render_context)
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
        call = lambda x: getattr(x, name) if x is not None else None
        new_ground_sprite = call(self.ground_sprite)
        new_sprites = [call(sprite) for sprite in self.parent_sprites]
        return ALayout(
            new_ground_sprite,
            new_sprites,
            self.traversable,
            self.category,
            self.notes,
            altitude=self.altitude,
            foundation=call(self.foundation),
        )

    def __call__(self, *args, **kwargs):
        call = lambda x: x(*args, **kwargs) if x is not None else None
        new_ground_sprite = call(self.ground_sprite)
        new_sprites = [call(sprite) for sprite in self.parent_sprites]
        return ALayout(
            new_ground_sprite,
            new_sprites,
            self.traversable,
            self.category,
            self.notes,
            altitude=self.altitude,
            foundation=call(self.foundation),
        )

    def __add__(self, parent_sprite):
        ret = replace(self, parent_sprites=self.parent_sprites + [parent_sprite])
        ret.__class__ = ALayout
        return ret

    @property
    def sprites(self):
        return unique(sub for s in [self.ground_sprite] + self.parent_sprites for sub in s.sprites)

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

        assert layout is not None

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
