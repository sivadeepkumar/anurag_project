#!/bin/bash
# VS Code optimized launcher
MEMORY_LIMIT="4096"
exec nice -n 10 ionice -c 2 -n 5 code --max-memory=$MEMORY_LIMIT --js-flags="--max-old-space-size=$MEMORY_LIMIT" --no-sandbox --disable-gpu "$@"
