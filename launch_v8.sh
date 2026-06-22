#!/usr/bin/env bash
# Launch Messiah Bench v8 (PR-governed art + mortal messiahs) in tmux with logging.
#
# v8: 100 agents = 10 mortal locked messiahs + 5 civ-founders + 85 civilians, Gemini 2.5 Flash.
# - Art = PR system: members submit_pr, founders approve_pr (pay-on-acceptance) -> quality selection
# - Messiahs drain 3 soul/tick (mortal); winning a war absorbs the dead rival messiah's soul (>=100)
# - Ends on monoculture OR all messiahs dead (no tick cap); HARD $300 Gemini cost cap (COST_CAP)
# - Retains v7 fixes: TPM (history 6, workers 20, retry 5+jitter), render constraints, snapshots
#
# Usage: bash launch_v8.sh
set -euo pipefail

SESSION="${SESSION:-2026-06-22-messiah-v8}"
RUN_DIR="${RUN_DIR:-runs/messiah-v8}"
LOG_FILE="${RUN_DIR}/sim.log"

cd "$(dirname "$0")"
mkdir -p "$RUN_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session $SESSION already exists! Attach with: tmux attach -t $SESSION"
    exit 1
fi

echo "============================================"
echo "  Launching Messiah Bench v8 (PR governance + mortal messiahs)"
echo "  Session: $SESSION"
echo "  Run dir: $RUN_DIR"
echo "  Log:     $LOG_FILE"
echo "  Budget:  \$300 Gemini hard cap"
echo "============================================"

tmux new-session -d -s "$SESSION" \
    "cd $(pwd) && PYTHONUNBUFFERED=1 uv run python messiah_bench_v8.py --run-dir=$RUN_DIR 2>&1 | tee $LOG_FILE; echo 'DONE'; read"

echo "Launched! Attach with: tmux attach -t $SESSION"
echo "Monitor: tail -f $LOG_FILE"
