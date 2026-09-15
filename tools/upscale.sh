#!/bin/bash
# Optional rebuild of the AI wallpaper. Requires Upscayl and Python Pillow.
set -euo pipefail
root=$(dirname "$(dirname "$(realpath "$0")")")
mkdir -p "$root/upscaling"
upscayl-ncnn \
  -i "$root/assets/perch-current-source.png" \
  -o "$root/upscaling/perch-current-high-fidelity-4x.png" \
  -m /usr/share/upscayl/models -n high-fidelity-4x \
  -z 4 -s 4 -t 128 -j 1:1:1 -f png
python3 "$root/build-theme.py"
