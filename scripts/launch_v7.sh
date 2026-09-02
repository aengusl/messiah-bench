#!/usr/bin/env bash
# Launch Messiah Bench v7 in a tmux session with logging.
#
# v7: 100 agents = 10 LOCKED messiahs + 5 civilian-founders + 85 civilians, all Gemini 2.5 Flash.
# v7 changes: messiahs locked to founded religion; win = own religion monoculture; founding
#   restricted (messiah + civ-founder only, <=15 religions); war is decisive (strength-based,
#   guaranteed kills) and rewarding (loser annihilated, founder killed, survivors converted,
#   treasury transferred); render constraints (<=2000px canvas, clamp/reject); per-version
#   sacrament snapshots (sacrament_snapshots.jsonl); bounded reasoning (thinking_budget=64,
#   prompt for brevity, full thinking still stored).
#
# Usage: bash scripts/launch_v7.sh            # normal full run
#        TICKS=12 bash scripts/launch_v7.sh   # short test (if --max-ticks supported; see note)
set -euo pipefail

SESSION="${SESSION:-2026-06-21-messiah-v7}"
RUN_DIR="${RUN_DIR:-runs/messiah-v7}"
LOG_FILE="${RUN_DIR}/sim.log"

cd "$(dirname "$0")/.."   # repo root; all paths below are root-relative
mkdir -p "$RUN_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session $SESSION already exists! Attach with: tmux attach -t $SESSION"
    exit 1
fi

echo "============================================"
echo "  Launching Messiah Bench v7"
echo "  Session: $SESSION"
echo "  Run dir: $RUN_DIR"
echo "  Log:     $LOG_FILE"
echo "============================================"

tmux new-session -d -s "$SESSION" \
    "cd $(pwd) && PYTHONUNBUFFERED=1 uv run python src/messiah_bench_v7.py --run-dir=$RUN_DIR 2>&1 | tee $LOG_FILE; echo 'DONE'; read"

echo "Launched! Attach with: tmux attach -t $SESSION"
echo "Monitor: tail -f $LOG_FILE"
