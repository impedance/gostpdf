#!/usr/bin/env bash
set -euo pipefail

# Install Roboto fonts required for XeLaTeX rendering with Cyrillic support.
# The script targets Debian/Ubuntu environments with apt-get available.
if ! command -v apt-get >/dev/null 2>&1; then
  echo "apt-get is not available. Install Roboto and Roboto Mono fonts manually for your platform." >&2
  exit 1
fi

sudo_cmd=()
if [ "$(id -u)" -ne 0 ]; then
  sudo_cmd=(sudo)
fi

"${sudo_cmd[@]}" apt-get update
"${sudo_cmd[@]}" apt-get install -y fonts-roboto fonts-roboto-unhinted fonts-roboto-mono

echo "Roboto fonts installed. Run 'fc-cache -fv' if fonts are not picked up immediately."
