#!/usr/bin/env bash
# Stage the HF cache entries the task image needs into hf/ (gitignored build input).
# Hardlinks when on the same filesystem; the HF cache layout (blobs + snapshot symlinks) is kept.
set -euo pipefail
SRC="${1:-$HOME/hf_home/hub}"
DST="$(dirname "$0")/../hf/hub"
mkdir -p "$DST"
for m in models--google--gemma-2-2b models--google--gemma-scope-2b-pt-res; do
    cp -al "$SRC/$m" "$DST/" 2>/dev/null || cp -a "$SRC/$m" "$DST/"
done
du -shL "$DST"
