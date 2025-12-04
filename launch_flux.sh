#!/bin/bash

Flux Pipeline Launcher for Mac/Linux

--- 1. Pipeline Configuration ---

export FLUX_ROOT="/mnt/server/projects"

Adjust Nuke path for your system

NUKE_PATH="/Applications/Nuke15.0v4/Nuke15.0v4.app/Contents/MacOS/Nuke15.0"

--- 2. Set Context ---

if [ -z "$1" ]; then
echo "[Flux] No Project specified. Launching in Default Context."
export FLUX_PROJECT="TMP"
export FLUX_SHOT="000_000"
else
export FLUX_PROJECT="$1"
export FLUX_SHOT="$2"
fi

echo "=========================================="
echo "  FLUX PIPELINE LAUNCHER"
echo "=========================================="
echo "  ROOT    : $FLUX_ROOT"
echo "  PROJECT : $FLUX_PROJECT"
echo "  SHOT    : $FLUX_SHOT"
echo "=========================================="

--- 3. Launch Nuke ---

"$NUKE_PATH" --nukex