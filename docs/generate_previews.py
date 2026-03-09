"""Generate preview images for AGRF documentation.

This script creates Demo instances showcasing empty grounds, railways, slopes,
and foundations across various climates, then renders them as PNG images for
inclusion in the Sphinx documentation.
"""

import os

from agrf.lib.building.layout import ADefaultGroundSprite, ALayout
from agrf.lib.building.demo import Demo

IMG_DIR = os.path.join(os.path.dirname(__file__), "img")
SCALE = 4
BPP = 32


def make_layout(sprite_id):
    return ALayout(ADefaultGroundSprite(sprite_id), [], True)


def save_demo(demo, filename):
    path = os.path.join(IMG_DIR, filename)
    img = demo.graphics(SCALE, BPP).crop().to_pil_image()
    img.save(path)
    print(f"  {filename}: {img.size}")


def generate_empty_grounds():
    """Generate empty ground tiles for each climate."""
    print("Generating empty grounds...")
    ground = make_layout(3981)
    for climate in ["temperate", "tropical", "toyland"]:
        demo = Demo(
            tiles=[[ground, ground], [ground, ground]],
            title=f"{climate} ground",
            climate=climate,
        )
        save_demo(demo, f"ground_{climate}.png")

    # Arctic uses rail sprite 1012 as ground because arctic/3981.png has a
    # non-standard size that causes rendering issues.
    arctic_ground = make_layout(1012)
    demo = Demo(
        tiles=[[arctic_ground, arctic_ground], [arctic_ground, arctic_ground]],
        title="arctic ground",
        climate="arctic",
    )
    save_demo(demo, "ground_arctic.png")


def generate_railways():
    """Generate railway demos for different climates and rail types."""
    print("Generating railways...")
    rail_x = make_layout(1011)
    rail_y = make_layout(1012)

    for climate in ["temperate", "arctic", "tropical", "toyland"]:
        demo = Demo(
            tiles=[[rail_x, rail_y]],
            title=f"{climate} railway",
            climate=climate,
        )
        save_demo(demo, f"railway_{climate}.png")

    # Snow subclimate
    demo = Demo(
        tiles=[[rail_x, rail_y]],
        title="arctic snow railway",
        climate="arctic",
        subclimate="snow",
    )
    save_demo(demo, "railway_arctic_snow.png")

    # Monorail and maglev
    for rail_type in ["monorail", "maglev"]:
        demo = Demo(
            tiles=[[rail_x, rail_y]],
            title=f"{rail_type} railway",
            climate="temperate",
            rail_type=rail_type,
        )
        save_demo(demo, f"railway_{rail_type}.png")


def generate_slopes():
    """Generate slope demos with various altitude configurations."""
    print("Generating slopes...")
    ground = make_layout(3981)

    # Single-tile slopes in each direction
    slopes = {
        "slope_W": [[1, 0], [0, 0]],
        "slope_S": [[0, 0], [1, 0]],
        "slope_E": [[0, 0], [0, 1]],
        "slope_N": [[0, 1], [0, 0]],
    }
    for name, altitude in slopes.items():
        demo = Demo(
            tiles=[[ground]],
            title=name,
            climate="temperate",
            altitude=altitude,
        )
        save_demo(demo, f"{name}.png")

    # Multi-tile slope: hill
    demo = Demo(
        tiles=[[ground] * 3] * 3,
        title="hill",
        climate="temperate",
        altitude=[
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
    )
    save_demo(demo, "slope_hill.png")

    # Multi-tile slope: ridge
    demo = Demo(
        tiles=[[ground] * 3] * 2,
        title="ridge",
        climate="temperate",
        altitude=[
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
    )
    save_demo(demo, "slope_ridge.png")


def generate_foundations():
    """Generate foundation demos with railways on slopes."""
    print("Generating foundations...")
    rail = make_layout(1012)

    # Railways on a hill (foundations are automatically added)
    demo = Demo(
        tiles=[[rail] * 3] * 3,
        title="foundation hill",
        climate="temperate",
        altitude=[
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
    )
    save_demo(demo, "foundation_hill.png")

    # Railways on a slope edge
    demo = Demo(
        tiles=[[rail, rail]],
        title="foundation edge",
        climate="temperate",
        altitude=[
            [0, 0, 0],
            [0, 1, 0],
        ],
    )
    save_demo(demo, "foundation_edge.png")

    # Arctic foundations with snow
    demo = Demo(
        tiles=[[rail] * 3] * 3,
        title="arctic foundation hill",
        climate="arctic",
        subclimate="snow",
        altitude=[
            [0, 0, 0, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 0, 0, 0],
        ],
    )
    save_demo(demo, "foundation_arctic_snow.png")


def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    generate_empty_grounds()
    generate_railways()
    generate_slopes()
    generate_foundations()
    print("Done!")


if __name__ == "__main__":
    main()
