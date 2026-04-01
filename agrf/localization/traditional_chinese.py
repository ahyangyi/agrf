import argparse
import os
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Convert simplified Chinese to OpenTTD-flavored Traditional Chinese using opencc"
    )
    parser.add_argument("-i", "--input", required=True, help="Input file")
    parser.add_argument("-o", "--output", required=True, help="Output file")
    args = parser.parse_args()

    config_path = os.path.join(os.path.dirname(__file__), "opencc_config", "s2t.json")
    subprocess.run(["opencc", "-i", args.input, "-o", args.output, "-c", config_path], check=True)


if __name__ == "__main__":
    sys.exit(main())
