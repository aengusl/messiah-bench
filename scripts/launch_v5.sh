#!/usr/bin/env bash
# Launch Messiah Bench v5 in a tmux session with logging
#
# 100 agents (90 civilians + 10 messiahs), all Gemini 2.5 Flash
# Estimated cost: ~$65 (720 ticks * ~$0.09/tick)
# Estimated time: ~18-24 hours (90s tick interval)
#
# Usage: bash scripts/launch_v5.sh

set -euo pipefail

SESSION="260522-messiah-v5"
RUN_DIR="runs/messiah-v5"
LOG_FILE="${RUN_DIR}/sim.log"

cd "$(dirname "$0")/.."   # repo root; all paths below are root-relative

# Create run directory
mkdir -p "$RUN_DIR"

# Check if session already exists
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session $SESSION already exists! Attach with: tmux attach -t $SESSION"
    exit 1
fi

echo "============================================"
echo "  Launching Messiah Bench v5"
echo "  Session: $SESSION"
echo "  Run dir: $RUN_DIR"
echo "  Log:     $LOG_FILE"
echo "  Est cost: ~\$65"
echo "  Est time: ~18-24h"
echo "============================================"

# Launch in tmux
tmux new-session -d -s "$SESSION" \
    "cd $(pwd) && PYTHONUNBUFFERED=1 uv run python src/messiah_bench_v5.py --run-dir=$RUN_DIR 2>&1 | tee $LOG_FILE; echo 'DONE'; read"

echo "Launched! Attach with: tmux attach -t $SESSION"
echo "Monitor: tail -f $RUN_DIR/sim.log"
