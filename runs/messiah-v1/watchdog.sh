#!/bin/bash
# Watchdog for messiah-bench: detect stuck simulation
# Usage: bash runs/messiah-v1/watchdog.sh
# Returns exit code 1 if stuck (no update for 10+ minutes)

DIR="$(cd "$(dirname "$0")" && pwd)"
STATE="$DIR/world_state.json"
STUCK_THRESHOLD=600  # 10 minutes in seconds

if [ ! -f "$STATE" ]; then
    echo "WATCHDOG: No world_state.json -- simulation not started"
    exit 0
fi

# Check last modification time
NOW=$(date +%s)
LAST_MOD=$(stat -c '%Y' "$STATE" 2>/dev/null || stat -f '%m' "$STATE" 2>/dev/null)

if [ -z "$LAST_MOD" ]; then
    echo "WATCHDOG: Cannot read file modification time"
    exit 1
fi

AGE=$((NOW - LAST_MOD))

# Check if simulation has a winner (finished)
WINNER=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('winner',''))" 2>/dev/null)
if [ -n "$WINNER" ] && [ "$WINNER" != "" ] && [ "$WINNER" != "None" ]; then
    echo "WATCHDOG OK: Simulation complete. Winner declared."
    exit 0
fi

# Check tick count
TICK=$(python3 -c "import json; d=json.load(open('$STATE')); print(d['tick'])" 2>/dev/null || echo "0")

if [ "$AGE" -gt "$STUCK_THRESHOLD" ]; then
    echo "WATCHDOG ALERT: Simulation appears STUCK"
    echo "  Last update: ${AGE}s ago (threshold: ${STUCK_THRESHOLD}s)"
    echo "  Current tick: $TICK"
    echo "  State file: $STATE"
    echo ""
    echo "  Possible causes:"
    echo "    - Process crashed (check tmux session)"
    echo "    - API rate limit hit"
    echo "    - Cost cap exceeded"
    echo ""
    echo "  To check: ps aux | grep messiah_bench"
    echo "  To restart: uv run python messiah_bench.py  (will resume from tick $TICK)"
    exit 1
else
    echo "WATCHDOG OK: Last update ${AGE}s ago. Tick $TICK."
    exit 0
fi
