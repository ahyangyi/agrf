import grf
import numpy as np
import json
from PIL import Image
from agrf.lib.building.registers import Registers
from agrf.lib.building.layout import AGroundSprite, ADefaultGroundSprite, AParentSprite, AChildSprite, ALayout
from agrf.lib.building.symmetry import BuildingSymmetrical
from agrf.lib.building.image_sprite import image_sprite
from agrf.graphics.misc import SCALE_TO_ZOOM

temperate_1011 = np.array(Image.open("agrf/third_party/opengfx2/temperate/1011.png"))
temperate_1012 = np.array(Image.open("agrf/third_party/opengfx2/temperate/1012.png"))
temperate_1011_over_1012 = np.array(
    Image.alpha_composite(Image.fromarray(temperate_1012), Image.fromarray(temperate_1011))
)


dgs1012 = ADefaultGroundSprite(1012)
gs1012 = AGroundSprite(image_sprite("agrf/third_party/opengfx2/temperate/1012.png"))
ps1012 = AParentSprite(image_sprite("agrf/third_party/opengfx2/temperate/1012.png"), (16, 16, 1), (0, 0, 0))
ch1011snow = AChildSprite(
    image_sprite("agrf/third_party/opengfx2/temperate/1011.png"), (0, 0), flags={"dodraw": Registers.SNOW}
)
l1012 = ALayout(dgs1012, [], True)
l1012snow = ALayout(gs1012 + ch1011snow, [], True)
pl1012 = ALayout(None, [ps1012], True)
pl1012snow = ALayout(None, [ps1012 + ch1011snow], [], True)


def test_default_groundsprite():
    assert (temperate_1012 == dgs1012.graphics(4, 32).to_image()).all()


def test_default_groundsprite_M():
    assert (temperate_1011 == dgs1012.M.graphics(4, 32).to_image()).all()


def test_default_groundsprite_R():
    assert (temperate_1012 == dgs1012.R.graphics(4, 32).to_image()).all()


def test_default_groundsprite_T():
    assert (temperate_1012 == dgs1012.T.graphics(4, 32).to_image()).all()


def test_groundsprite():
    assert (temperate_1012 == gs1012.graphics(4, 32).to_image()).all()


def test_groundsprite_to_grf():
    assert isinstance(gs1012.to_grf(gs1012.sprites)[0], grf.GroundSprite)


def test_groundsprite_to_action2():
    assert isinstance(gs1012.to_action2(gs1012.sprites)[0]["sprite"], grf.SpriteRef)


def test_groundsprite_fingerprint():
    json.dumps(gs1012.get_fingerprint())


def test_groundsprite_get_resource_files():
    assert all(isinstance(file, grf.ResourceFile) for file in gs1012.get_resource_files())


def test_parentsprite():
    assert (temperate_1012 == ps1012.graphics(4, 32).to_image()).all()


def test_parentsprite_to_grf():
    assert isinstance(ps1012.to_grf(ps1012.sprites)[0], grf.ParentSprite)


def test_parentsprite_to_action2():
    assert isinstance(ps1012.to_action2(ps1012.sprites)[0]["sprite"], grf.SpriteRef)


def test_parentsprite_fingerprint():
    json.dumps(ps1012.get_fingerprint())


def test_parentsprite_get_resource_files():
    assert all(isinstance(file, grf.ResourceFile) for file in ps1012.get_resource_files())


def test_parentsprite_add_none():
    assert (ps1012 + None) is ps1012


def test_layout():
    assert (temperate_1012 == l1012.graphics(4, 32).to_image()).all()


def test_layout_M():
    assert (temperate_1011 == l1012.M.graphics(4, 32).to_image()).all()


def test_layout_R():
    assert (temperate_1012 == l1012.R.graphics(4, 32).to_image()).all()


def test_layout_T():
    assert (temperate_1012 == l1012.T.graphics(4, 32).to_image()).all()


def test_default_ground_sprite_to_parentsprite():
    # For now, just make sure this can run
    dgs1012.to_parentsprite()


def test_layout_snow():
    assert (temperate_1012 == l1012snow.graphics(4, 32).to_image()).all()


def test_layout_snow_arctic():
    assert (temperate_1011_over_1012 == l1012snow.graphics(4, 32, climate="arctic", subclimate="snow").to_image()).all()


def test_layout_snow_arctic_filter():
    assert (
        temperate_1012
        == l1012snow.filter_register(Registers.SNOW).graphics(4, 32, climate="arctic", subclimate="snow").to_image()
    ).all()


def test_playout_snow():
    assert (temperate_1012 == pl1012snow.graphics(4, 32).to_image()).all()


def test_playout_snow_arctic():
    assert (
        temperate_1011_over_1012 == pl1012snow.graphics(4, 32, climate="arctic", subclimate="snow").to_image()
    ).all()


def test_playout_snow_arctic_filter():
    assert (
        temperate_1012
        == pl1012snow.filter_register(Registers.SNOW).graphics(4, 32, climate="arctic", subclimate="snow").to_image()
    ).all()


def test_ground_sprite_to_parentsprite():
    # For now, just make sure this can run
    gs1012.to_parentsprite()


def test_pushdown():
    # FIXME also examine the offsets
    assert (temperate_1012 == ps1012.pushdown(1).graphics(4, 32).to_image()).all()


def test_symmetry():
    gs1012 = ADefaultGroundSprite(1012)
    gs1011 = ADefaultGroundSprite(1011)

    g = BuildingSymmetrical.create_variants([gs1012, gs1011])
    assert g is g.R
    assert g is g.T
    assert g is g.M.M
