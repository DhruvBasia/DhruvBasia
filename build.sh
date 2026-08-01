#!/usr/bin/env bash
# Regenerate everything. Pass a photo to also rebuild the portrait:
#   ./build.sh                 -> heatmap + info card
#   ./build.sh me.jpg          -> heatmap + info card + ASCII portrait
set -euo pipefail
cd "$(dirname "$0")"

if [ $# -ge 1 ]; then
  python scripts/prep_photo.py "$1"
fi
python scripts/make_ascii_svg.py
python scripts/make_info_card.py
python scripts/fetch_contributions.py
python scripts/render_heatmap_svg.py
echo "done -- open preview.html to check the animations"
