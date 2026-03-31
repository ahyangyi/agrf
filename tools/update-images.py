#!/usr/bin/env python3
"""
Script to download OpenGFX2 High Definition graphics for use as base images.

Downloads OpenGFX2 from GitHub releases if not already present,
verifies the SHA256 checksum, extracts to tools/.baseset, and
extracts 4x sprites to tools/.output.
"""

import hashlib
import os
import shutil
import sys
import tarfile
from pathlib import Path
from urllib.request import urlretrieve

sys.path.insert(0, str(Path(__file__).parent))
from extract_4x_sprites import extract_from_grf

# Configuration
CACHE_DIR = Path(__file__).parent / ".cache"
BASESET_DIR = Path(__file__).parent / ".baseset"
OUTPUT_DIR = Path(__file__).parent / ".output"
DOWNLOAD_URL = "https://github.com/OpenTTD/OpenGFX2/releases/download/0.8.1/OpenGFX2_HighDef-0.8.1.tar"
FILENAME = "OpenGFX2_HighDef-0.8.1.tar"
EXPECTED_SHA256 = "c1f5066e82b7754d29f7637457f5b77ac71f10198e3a38f7a75353ea62386e2d"

GRF_FILES = [
    "ogfx21_base_32ez.grf",
    "ogfx2c_arctic_32ez.grf",
    "ogfx2e_extra_32ez.grf",
    "ogfx2h_tropical_32ez.grf",
    "ogfx2i_logos_32ez.grf",
    "ogfx2t_toyland_32ez.grf",
]


def sha256_file(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def download_file(url: str, dest: Path) -> None:
    """Download a file from URL to destination."""
    print(f"Downloading {url}...")
    print(f"Destination: {dest}")

    def progress_hook(count, block_size, total_size):
        percent = min(int(count * block_size * 100 / total_size), 100)
        sys.stdout.write(f"\rProgress: {percent}%")
        sys.stdout.flush()

    urlretrieve(url, dest, reporthook=progress_hook)
    print()  # New line after progress


def clear_directory(dir_path: Path) -> None:
    """Clear all contents of a directory."""
    if not dir_path.exists():
        return

    print(f"Clearing {dir_path}...")
    for item in dir_path.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def extract_tar(tar_path: Path, dest_dir: Path) -> None:
    """Extract tar file to destination directory, flattening the top-level directory."""
    print(f"Extracting {tar_path.name} to {dest_dir}...")

    dest_dir.mkdir(parents=True, exist_ok=True)
    clear_directory(dest_dir)

    with tarfile.open(tar_path, "r") as tar:
        for member in tar.getmembers():
            if member.name == "." or "/" not in member.name:
                continue
            parts = member.name.split("/", 1)
            if len(parts) > 1:
                member.name = parts[1]
            else:
                continue
            tar.extract(member, path=dest_dir, filter="fully_trusted")

    print("✓ Extraction complete.")


def extract_all_sprites() -> None:
    """Extract 4x sprites from all GRF files to OUTPUT_DIR."""
    print(f"\nExtracting sprites to {OUTPUT_DIR}...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    clear_directory(OUTPUT_DIR)

    for grf_name in GRF_FILES:
        grf_path = BASESET_DIR / grf_name
        if not grf_path.exists():
            print(f"  Warning: {grf_name} not found, skipping.")
            continue

        grf_output_dir = OUTPUT_DIR / grf_name.replace(".grf", "")
        print(f"  Extracting {grf_name}...")
        extract_from_grf(grf_path, grf_output_dir)

    print("✓ Sprite extraction complete.")


CLIMATE_PATTERN_MAP = {0: "temperate", 1: "arctic", 2: "tropical", 3: "toyland"}
CLIMATE_GROUND_PATTERN_MAP = {5: "temperate", 6: "arctic", 7: "tropical", 8: "toyland"}
THIRD_PARTY_DIR = Path(__file__).parent.parent / "agrf" / "third_party" / "opengfx2"


def copy_extra_sprites():
    """Copy sprites from ogfx2e_extra_32ez to third_party/opengfx2."""
    print(f"\nCopying extra sprites to {THIRD_PARTY_DIR}...")

    extra_dir = OUTPUT_DIR / "ogfx2e_extra_32ez"
    if not extra_dir.exists():
        print(f"  Warning: {extra_dir} not found, skipping copy.")
        return

    THIRD_PARTY_DIR.mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped = 0

    # climate pattern
    for x_range in [range(990, 1004), range(5413, 5503)]:
        for x in x_range:
            for y, climate in CLIMATE_PATTERN_MAP.items():
                src = extra_dir / f"{x}_{y}.png"
                climate_dir = THIRD_PARTY_DIR / climate
                climate_dir.mkdir(parents=True, exist_ok=True)
                dst = climate_dir / f"{x}.png"

                if src.exists():
                    shutil.copy2(src, dst)
                    copied += 1
                else:
                    skipped += 1

    # climate ground pattern
    for a in list(range(1011, 1227)) + list(range(1332, 1351)) + list(range(1370, 1398)):
        for b, climate in CLIMATE_GROUND_PATTERN_MAP.items():
            src = extra_dir / f"{a}_{b}.png"
            climate_dir = THIRD_PARTY_DIR / climate
            climate_dir.mkdir(parents=True, exist_ok=True)
            dst = climate_dir / f"{a}.png"

            if src.exists():
                shutil.copy2(src, dst)
                copied += 1
            else:
                skipped += 1

    print(f"✓ Copied {copied} sprites, skipped {skipped}.")


def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    tar_path = CACHE_DIR / FILENAME

    needs_download = True
    if tar_path.exists():
        print(f"File already exists: {tar_path}")
        print("Verifying checksum...")
        actual_sha256 = sha256_file(tar_path)

        if actual_sha256 == EXPECTED_SHA256:
            print("✓ Checksum verified. File is valid.")
            needs_download = False
        else:
            print("✗ Checksum mismatch!")
            print(f"  Expected: {EXPECTED_SHA256}")
            print(f"  Actual:   {actual_sha256}")
            print("Re-downloading...")
            tar_path.unlink()

    if needs_download:
        try:
            download_file(DOWNLOAD_URL, tar_path)
        except Exception as e:
            print(f"Error downloading file: {e}", file=sys.stderr)
            return 1

        print("Verifying checksum...")
        actual_sha256 = sha256_file(tar_path)

        if actual_sha256 != EXPECTED_SHA256:
            print("✗ Checksum mismatch!", file=sys.stderr)
            print(f"  Expected: {EXPECTED_SHA256}", file=sys.stderr)
            print(f"  Actual:   {actual_sha256}", file=sys.stderr)
            tar_path.unlink()
            return 1

        print("✓ Checksum verified. Download successful.")

    extract_tar(tar_path, BASESET_DIR)
    extract_all_sprites()
    copy_extra_sprites()

    return 0


if __name__ == "__main__":
    sys.exit(main())
