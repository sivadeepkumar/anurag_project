#!/bin/bash
# VS Code optimized launcher
# Usage: ./vscode-launcher.sh [workspace_path]

# Set memory limits and optimization flags
MEMORY_LIMIT="4096"

# Apply cgroup limits if available
if [ -d "/sys/fs/cgroup/memory/vscode" ]; then
  echo $$ | sudo tee /sys/fs/cgroup/memory/vscode/tasks > /dev/null
fi

# Launch with optimized settings
exec nice -n 10 ionice -c 2 -n 5 code \
  --max-memory=$MEMORY_LIMIT \
  --js-flags="--max-old-space-size=$MEMORY_LIMIT" \
  --no-sandbox \
  --disable-gpu \
  --disable-software-rasterizer \
  --disable-smooth-scrolling \
  --unity-launch \
  "$@" 