#!/usr/bin/env python3
"""
Script to extract 4x zoom sprites from OpenTTD GRF files.

Extracts:
- Base sprites (sequential IDs from data section)
- Action 5 sprites (extra sprites at specific base IDs)
- Action A replacements (overrides for base sprites)

Usage:
    python extract_4x_sprites.py <input.grf> [output_dir]

Output:
    Extracts 4x zoom 32bpp sprites to the specified directory (default: 'output'),
    with each sprite saved as a PNG file using the naming pattern:

    "{type}_{sprite_id}_{variant_id}_32.png" - for 32bpp RGBA
    "{type}_{sprite_id}_{variant_id}_p.png" - for accompanying palette (if present)

    - type: "00" for base/Action A sprites, or Action 5 type in hex (e.g., "06")
    - sprite_id: Base set sprite ID
    - variant_id: 0-N for multiple variants of the same sprite (e.g., climates)
"""

import argparse
import io
import struct
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image
from tqdm import tqdm

from grf.common import read_extended_byte, ZOOM_NORMAL
from grf.decompile import RealGraphicsSprite, decode_sprite, read, ParsingContext
from grf.colour import PIL_PALETTE
from agrf.graphics.layered_image import LayeredImage

SCRIPT_PATH = Path(__file__).resolve()
SUCCESS_MARKER = ".extraction-success"


# Action 5 base sprite IDs from OpenTTD src/newgrf/newgrf_act5.cpp
ACTION5_BASE_SPRITES = {
    0x04: 5088,  # SPR_SIGNALS_BASE - Signal graphics
    0x05: 5632,  # SPR_ELRAIL_BASE - Rail catenary graphics
    0x06: 5413,  # SPR_SLOPES_BASE - Foundation graphics
    0x08: 5328,  # SPR_CANALS_BASE - Canal graphics
    0x09: 6105,  # SPR_ONEWAY_BASE - One way road graphics
    0x0A: 5680,  # SPR_2CCMAP_BASE - 2CC colour maps
    0x0B: 5986,  # SPR_TRAMWAY_BASE - Tramway graphics
    0x0D: 5936,  # SPR_SHORE_BASE - Shore graphics
    0x0F: 5401,  # SPR_TRACKS_FOR_SLOPES_BASE - Sloped rail track
    0x10: 5954,  # SPR_AIRPORTX_BASE - Airport graphics
    0x11: 5978,  # SPR_ROADSTOP_BASE - Road stop graphics
    0x12: 5393,  # SPR_AQUEDUCT_BASE - Aqueduct graphics
    0x13: 5577,  # SPR_AUTORAIL_BASE - Autorail graphics
    0x15: 4896,  # SPR_OPENTTD_BASE - OpenTTD GUI graphics
    0x16: 5969,  # SPR_AIRPORT_PREVIEW_BASE - Airport preview graphics
    0x17: 6123,  # SPR_RAILTYPE_TUNNEL_BASE - Railtype tunnel base
    0x18: 6140,  # SPR_PALETTE_BASE - Palette
    0x19: 6141,  # SPR_ROAD_WAYPOINTS_BASE - Road waypoints
    0x1A: 6145,  # SPR_OVERLAY_ROCKS_BASE - Overlay rocks
    0x1B: 6240,  # SPR_BRIDGE_DECKS_BASE - Bridge decks
}


def decode_sprite_data(sprite: RealGraphicsSprite, f: io.BytesIO, container_version: int) -> Optional[np.ndarray]:
    """Decode sprite data from file."""
    f.seek(sprite.offset)

    try:
        data, _ = decode_sprite(f, sprite, container_version)
        return data
    except Exception as e:
        return None


def sprite_data_to_image(sprite: RealGraphicsSprite, data: np.ndarray) -> Optional[Image.Image]:
    """Convert decoded sprite numpy array to a PIL Image."""
    if data is None or data.size == 0:
        return None

    h, w = sprite.height, sprite.width

    # data shape is (height, width, bpp)
    has_rgb = sprite.type & 0x01
    has_alpha = sprite.type & 0x02
    has_mask = sprite.type & 0x04

    idx = 0
    rgb = None
    alpha = None
    mask = None

    if has_rgb:
        rgb = data[:, :, idx : idx + 3]
        idx += 3
    if has_alpha:
        alpha = data[:, :, idx]
        idx += 1
    if has_mask:
        mask = data[:, :, idx]
        idx += 1

    if rgb is not None and alpha is not None:
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        rgba[:, :, :3] = rgb
        rgba[:, :, 3] = alpha
        return Image.fromarray(rgba, mode="RGBA")

    if rgb is not None and mask is not None:
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        rgba[:, :, :3] = rgb
        rgba[:, :, 3] = np.where(mask > 0, 255, 0)
        return Image.fromarray(rgba, mode="RGBA")

    if rgb is not None:
        return Image.fromarray(rgb, mode="RGB")

    if mask is not None:
        img = Image.fromarray(mask, mode="P")
        img.putpalette(PIL_PALETTE)
        return img

    if alpha is not None:
        return Image.fromarray(alpha, mode="L")

    return None


def extract_from_grf(
    grf_path: Path,
    output_dir: Path,
    type_filter: Optional[int] = None,
    with_action_type: bool = False,
    with_bit_width: bool = False,
):
    """Extract 4x zoom sprites from a single GRF file."""
    marker_file = output_dir / SUCCESS_MARKER
    if marker_file.exists():
        script_mtime = SCRIPT_PATH.stat().st_mtime
        marker_mtime = marker_file.stat().st_mtime
        if marker_mtime > script_mtime:
            return

    print(f"Reading GRF: {grf_path}")

    with open(grf_path, "rb") as f:
        ctx = ParsingContext(baseset=False)
        gen, container, real_sprites, pseudo_sprites = read(f, context=ctx)
        container_version = getattr(container, "version", 2)

        # Build sprite mapping
        sprites_to_extract = []  # (file_id, type, sprite_id, variant_id, has_palette, grf_path)

        # === Action 5 sprites ===
        action5_entries = []
        type_variant_counters = defaultdict(int)
        entry_idx = 0

        for k, v in pseudo_sprites.items():
            if hasattr(v, "set_type"):
                set_type = v.set_type
                num_sprites = getattr(v, "count", 0)

                has_offset = bool(set_type & 0x80)
                set_type_clean = set_type & 0x7F if has_offset else set_type
                offset_val = getattr(v, "offset", None)

                base = ACTION5_BASE_SPRITES.get(set_type_clean, 0)
                actual_base = base + (offset_val if offset_val else 0)

                variant_id = type_variant_counters[set_type_clean]
                type_variant_counters[set_type_clean] += 1

                action5_entries.append((set_type_clean, actual_base, num_sprites, variant_id, entry_idx))
                entry_idx += 1

        # Map Action 5 sprites
        for entry in action5_entries:
            set_type, start_base, num_sprites, variant_id, group_idx = entry

            if type_filter is not None and set_type != type_filter:
                continue

            group_name = f"action5_{group_idx}"

            group_sprites = []
            for sprite_id in ctx.sprites:
                info = ctx.sprites[sprite_id]
                if info[1] == group_name:
                    group_sprites.append(sprite_id)

            group_sprites.sort()

            for offset_in_entry, file_id in enumerate(group_sprites):
                if offset_in_entry >= num_sprites:
                    break
                base_id = start_base + offset_in_entry

                if file_id in real_sprites:
                    sprite_list = real_sprites[file_id]
                    # Check for 4x zoom 32bpp (has RGB or alpha)
                    has_32bpp = any(s.zoom == 1 and ((s.type & 0x01) or (s.type & 0x02)) for s in sprite_list)
                    # Only save _p.png if mask accompanies 32bpp (not standalone 8bpp)
                    has_32bpp_with_mask = any(
                        s.zoom == 1 and ((s.type & 0x01) or (s.type & 0x02)) and (s.type & 0x04) for s in sprite_list
                    )

                    if has_32bpp:
                        sprites_to_extract.append((file_id, set_type, base_id, variant_id, has_32bpp_with_mask))

        # === Action A replacements ===
        # Build list of Action A entries with their line numbers
        action_a_entries = []
        entry_idx = 0
        for line, sprite in sorted(pseudo_sprites.items()):
            if hasattr(sprite, "sets"):
                for first_global, num_sprites in sprite.sets:
                    action_a_entries.append((line, first_global, num_sprites, entry_idx))
                    entry_idx += 1

        # Group file IDs by action_a entry (using group name like 'action_a_0', 'action_a_1', etc.)
        action_a_files_by_entry = {}  # entry_idx -> [file_ids]
        for file_id in sorted(ctx.sprites.keys()):
            info = ctx.sprites[file_id]
            if info[1] and "action_a" in info[1]:
                # Extract entry index from group name 'action_a_N'
                try:
                    entry_num = int(info[1].split("_")[2])
                    if entry_num not in action_a_files_by_entry:
                        action_a_files_by_entry[entry_num] = []
                    action_a_files_by_entry[entry_num].append(file_id)
                except (IndexError, ValueError):
                    pass

        if action_a_entries and (type_filter is None or type_filter == 0):
            for line, first_global, num_sprites, entry_idx in action_a_entries:
                if entry_idx not in action_a_files_by_entry:
                    continue

                file_ids = action_a_files_by_entry[entry_idx]

                for offset, file_id in enumerate(file_ids):
                    if offset >= num_sprites:
                        break

                    global_id = first_global + offset

                    if file_id in real_sprites:
                        sprite_list = real_sprites[file_id]
                        has_32bpp = any(s.zoom == 1 and ((s.type & 0x01) or (s.type & 0x02)) for s in sprite_list)
                        # Only save _p.png if mask accompanies 32bpp (not standalone 8bpp)
                        has_32bpp_with_mask = any(
                            s.zoom == 1 and ((s.type & 0x01) or (s.type & 0x02)) and (s.type & 0x04)
                            for s in sprite_list
                        )

                        if has_32bpp:
                            # variant_id is the index within this global_id
                            existing = [s for s in sprites_to_extract if s[2] == global_id and s[1] == 0]
                            variant_id = len(existing)
                            sprites_to_extract.append((file_id, 0, global_id, variant_id, has_32bpp_with_mask))

        # === Base sprites (sequential from data section) ===
        if type_filter is None or type_filter == 0:
            # Get Action 5 file IDs to exclude
            action5_file_ids = set(s[0] for s in sprites_to_extract)

            # Get Action A file IDs to exclude (they're already handled)
            action_a_file_ids = set(s[0] for s in sprites_to_extract if s[1] == 0)

            f.seek(0)
            first = f.read(1)
            header_bytes = first + f.read(9)
            data_offset, compression = struct.unpack("<IB", f.read(5))
            magic = f.read(4)
            version = struct.unpack("<I", f.read(4))[0]
            f.read(1)

            sequential_id = 1  # Start from 1, as OpenTTD's first sprite is at index 1

            while True:
                try:
                    num_data = f.read(4)
                    if len(num_data) < 4:
                        break
                    num = struct.unpack("<I", num_data)[0]

                    if num == 0:
                        break

                    grf_type = f.read(1)[0]

                    if grf_type == 0xFF:
                        f.seek(num, 1)
                        sequential_id += 1
                    elif grf_type == 0xFD:
                        ref_id = struct.unpack("<I", f.read(4))[0]

                        # Skip if this file ID is already handled by Action 5 or Action A
                        if ref_id not in action5_file_ids and ref_id not in action_a_file_ids:
                            if ref_id in real_sprites:
                                sprite_list = real_sprites[ref_id]
                                has_32bpp = any(
                                    s.zoom == 1 and ((s.type & 0x01) or (s.type & 0x02)) for s in sprite_list
                                )
                                # Only save _p.png if mask accompanies 32bpp (not standalone 8bpp)
                                has_32bpp_with_mask = any(
                                    s.zoom == 1 and ((s.type & 0x01) or (s.type & 0x02)) and (s.type & 0x04)
                                    for s in sprite_list
                                )

                                if has_32bpp:
                                    sprites_to_extract.append((ref_id, 0, sequential_id, 0, has_32bpp_with_mask))

                        sequential_id += 1
                    elif grf_type == 0xFC:
                        f.seek(4, 1)
                        # Sound references don't occupy sprite slots
                    else:
                        f.seek(num - 1, 1)
                        sequential_id += 1
                except Exception:
                    break

        print(f"Found {len(sprites_to_extract)} sprites to extract")

        if not sprites_to_extract:
            print("No sprites to extract.")
            return

        # Sort by type, sprite_id, variant_id
        sprites_to_extract.sort(key=lambda x: (x[1], x[2], x[3]))

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Extract sprites
        extracted_32bpp = 0
        extracted_pal = 0
        extracted_blended = 0
        skipped = 0

        for file_id, set_type, base_id, variant_id, has_pal in tqdm(sprites_to_extract, desc="Extracting"):
            if file_id not in real_sprites:
                skipped += 1
                continue

            sprite_list = real_sprites[file_id]

            # Find 4x zoom 32bpp and palette variants
            sprite_32bpp = None
            sprite_pal = None

            for sprite in sprite_list:
                if sprite.zoom != 1:  # Not 4x zoom
                    continue

                is_32bpp = (sprite.type & 0x01) and (sprite.type & 0x02)
                is_pal = sprite.type & 0x04

                if is_32bpp:
                    sprite_32bpp = sprite
                elif is_pal:
                    sprite_pal = sprite

            if not sprite_32bpp:
                skipped += 1
                continue

            # Decode and save 32bpp sprite
            data_32bpp = decode_sprite_data(sprite_32bpp, f, container_version)
            if data_32bpp is None:
                skipped += 1
                continue

            img_32bpp = sprite_data_to_image(sprite_32bpp, data_32bpp)
            if img_32bpp is None:
                skipped += 1
                continue

            prefix = f"{set_type:02x}_" if with_action_type else ""

            if with_bit_width:
                # Current behavior: save all variants with suffixes
                filename_32bpp = f"{prefix}{base_id}_{variant_id}_32.png"
                filepath_32bpp = output_dir / filename_32bpp
                img_32bpp.save(filepath_32bpp)
                extracted_32bpp += 1

                # Decode and save palette sprite if present
                if has_pal and sprite_pal:
                    data_pal = decode_sprite_data(sprite_pal, f, container_version)
                    if data_pal is not None:
                        img_pal = sprite_data_to_image(sprite_pal, data_pal)
                        if img_pal is not None:
                            filename_pal = f"{prefix}{base_id}_{variant_id}_p.png"
                            filepath_pal = output_dir / filename_pal
                            img_pal.save(filepath_pal)
                            extracted_pal += 1

                            # Create blended version using agrf's LayeredImage
                            try:
                                # Convert images to numpy arrays
                                arr_32bpp = np.array(img_32bpp)
                                arr_pal = np.array(img_pal)

                                # Extract RGB and alpha from 32bpp
                                rgb = arr_32bpp[:, :, :3]
                                alpha = arr_32bpp[:, :, 3]

                                # Use palette image as mask
                                mask = arr_pal

                                # Create LayeredImage and apply mask
                                li = LayeredImage(
                                    xofs=sprite_32bpp.xofs,
                                    yofs=sprite_32bpp.yofs,
                                    w=rgb.shape[1],
                                    h=rgb.shape[0],
                                    rgb=rgb.copy(),
                                    alpha=alpha.copy(),
                                    mask=mask.copy(),
                                )
                                li.apply_mask()

                                # Save blended image
                                img_blended = Image.fromarray(li.to_image())
                                filename_blended = f"{prefix}{base_id}_{variant_id}_b.png"
                                filepath_blended = output_dir / filename_blended
                                img_blended.save(filepath_blended)
                                extracted_blended += 1
                            except Exception as e:
                                # If blending fails, just skip the blended version
                                pass
            else:
                # New default behavior: only save one "best" variant without suffix
                # Priority: blended > 32bpp > palette

                # Decode palette sprite if present (needed for blending)
                img_pal = None
                if has_pal and sprite_pal:
                    data_pal = decode_sprite_data(sprite_pal, f, container_version)
                    if data_pal is not None:
                        img_pal = sprite_data_to_image(sprite_pal, data_pal)
                        if img_pal is not None:
                            extracted_pal += 1

                # Try to create blended version if palette exists
                img_to_save = None
                if img_pal is not None:
                    try:
                        # Convert images to numpy arrays
                        arr_32bpp = np.array(img_32bpp)
                        arr_pal = np.array(img_pal)

                        # Extract RGB and alpha from 32bpp
                        rgb = arr_32bpp[:, :, :3]
                        alpha = arr_32bpp[:, :, 3]

                        # Use palette image as mask
                        mask = arr_pal

                        # Create LayeredImage and apply mask
                        li = LayeredImage(
                            xofs=sprite_32bpp.xofs,
                            yofs=sprite_32bpp.yofs,
                            w=rgb.shape[1],
                            h=rgb.shape[0],
                            rgb=rgb.copy(),
                            alpha=alpha.copy(),
                            mask=mask.copy(),
                        )
                        li.apply_mask()

                        # Save blended image
                        img_to_save = Image.fromarray(li.to_image())
                        extracted_blended += 1
                    except Exception as e:
                        # If blending fails, fall back to 32bpp
                        img_to_save = img_32bpp
                        extracted_32bpp += 1
                else:
                    # No palette, use 32bpp
                    img_to_save = img_32bpp
                    extracted_32bpp += 1

                # Save the selected image without suffix
                filename = f"{prefix}{base_id}_{variant_id}.png"
                filepath = output_dir / filename
                img_to_save.save(filepath)

        print(f"\nExtraction complete:")
        print(f"  32bpp sprites: {extracted_32bpp}")
        print(f"  Palette sprites: {extracted_pal}")
        print(f"  Blended sprites: {extracted_blended}")
        print(f"  Skipped: {skipped}")

        marker_file.touch()


def main():
    parser = argparse.ArgumentParser(description="Extract 4x zoom sprites from OpenTTD GRF files")
    parser.add_argument("input_grf", type=Path, help="Input GRF file")
    parser.add_argument(
        "output_dir", type=Path, nargs="?", default=Path("output"), help="Output directory (default: output)"
    )
    parser.add_argument(
        "-t",
        "--type",
        type=lambda x: int(x, 0),
        dest="sprite_type",
        help="Filter by type (0x00 for base/Action A, 0x06 for foundations, etc.)",
    )
    parser.add_argument(
        "--with-action-type",
        action="store_true",
        help="Include action type prefix in filename (e.g., '00_' for base sprites, '06_' for foundations)",
    )
    parser.add_argument(
        "--with-bit-width",
        action="store_true",
        help="Include bit width suffix in filename (_32, _p, _b). By default, only the best variant is saved without suffix",
    )

    args = parser.parse_args()

    if not args.input_grf.exists():
        print(f"Error: File not found: {args.input_grf}")
        sys.exit(1)

    extract_from_grf(args.input_grf, args.output_dir, args.sprite_type, args.with_action_type, args.with_bit_width)


if __name__ == "__main__":
    main()
