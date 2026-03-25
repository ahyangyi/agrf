#!/usr/bin/env python
"""Generate documentation for AGRF."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agrf.lib.building.baseset_layouts import grassland_tile, railroad_tile
from agrf.lib.building.demo import Demo


def gen_docs():
    prefix = "docs/"
    img_prefix = os.path.join(prefix, "img", "baseset")
    os.makedirs(img_prefix, exist_ok=True)

    demos = [
        ("default", Demo(tiles=[[grassland_tile]], title="Default Tile")),
        ("railroad", Demo(tiles=[[railroad_tile]], title="Railroad Tile")),
    ]

    for name, demo in demos:
        img = demo.graphics(4, 32).crop().to_pil_image()
        img.save(os.path.join(img_prefix, f"{name}.png"))

    with open(os.path.join(prefix, "baseset_sprites.md"), "w") as f:
        f.write("# Base Set Sprites\n\n")
        for name, demo in demos:
            f.write(f"## {demo.title}\n\n")
            f.write(f"![{demo.title}](img/baseset/{name}.png)\n\n")

    print("Documentation generated.")


if __name__ == "__main__":
    gen_docs()
