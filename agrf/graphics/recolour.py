import grf
import functools


class ColourRange:
    def __init__(self, a, b=None):
        if b is None:
            b = a
        self.a = a
        self.b = b

    def __str__(self):
        return f"{self.a}-{self.b}"


class ColourMap:
    def __init__(self, name, colour_map):
        self.name = name
        self.colour_map = colour_map

    def positor_config(self):
        return {
            "input_ramp": ",".join(str(x) for x, _ in self.colour_map),
            "output_ramp": ",".join(str(x) for _, x in self.colour_map),
        }

    @functools.cache
    def __add__(self, o):
        return ColourMap(f"({self.name}+{o.name})", self.colour_map + o.colour_map)

    def to_sprite(self):
        triplets = []
        for f, t in self.colour_map:
            if f.a == f.b:
                triplets.append((f.a - 2, f.a - 2, t.a - 2))
            else:
                for i in range(f.a, f.b + 1):
                    triplets.append(
                        (i - 2, i - 2, ((i - f.a) * (t.b - t.a) + (f.b - f.a) // 2) // (f.b - f.a) + t.a - 2)
                    )
        return grf.PaletteRemap(triplets)


CC1_BLACK = ColourMap("cc1_black", [(ColourRange(0xC8, 0xCF), ColourRange(3, 8))])

CC2_BLACK = ColourMap("cc2_black", [(ColourRange(0x52, 0x59), ColourRange(3, 8))])

PROCESS_COLOUR = ColourMap("process", [(ColourRange(0x1, 0xFF), ColourRange(217))])
NON_RENDERABLE_COLOUR = ColourMap("non_renderable", [(ColourRange(0x1, 0xFF), ColourRange(255))])
