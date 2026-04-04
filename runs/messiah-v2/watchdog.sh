#!/bin/bash
# Watchdog for Messiah Bench v2 -- checks health every 5 minutes
# Usage: ./watchdog.sh

RUN_DIR="$(dirname "$0")"
STATE_FILE="$RUN_DIR/world_state.json"
LOG_FILE="$RUN_DIR/sim.log"
WATCHDOG_LOG="$RUN_DIR/watchdog.log"
STALE_THRESHOLD=900  # 15 minutes = stale

echo "=== Messiah Bench v2 Watchdog ===" | tee -a "$WATCHDOG_LOG"
echo "Started at $(date)" | tee -a "$WATCHDOG_LOG"
echo "Checking every 5 minutes. Stale threshold: ${STALE_THRESHOLD}s" | tee -a "$WATCHDOG_LOG"

while true; do
    NOW=$(date +%s)
    NOW_STR=$(date '+%Y-%m-%d %H:%M:%S')

    if [ ! -f "$STATE_FILE" ]; then
        echo "[$NOW_STR] WARNING: No world_state.json" | tee -a "$WATCHDOG_LOG"
        sleep 300
        continue
    fi

    # Check state file freshness
    STATE_MOD=$(stat -c %Y "$STATE_FILE" 2>/dev/null || echo 0)
    AGE=$((NOW - STATE_MOD))

    # Read state
    TICK=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d['tick'])" 2>/dev/null || echo "?")
    ALIVE=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(sum(1 for a in d['agents'] if a['alive']))" 2>/dev/null || echo "?")
    DEAD=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(len(d['graveyard']))" 2>/dev/null || echo "?")
    WARS=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(sum(1 for w in d.get('wars',[]) if w['rounds_remaining']>0))" 2>/dev/null || echo "?")
    WINNER=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); w=d.get('winner'); print(w['winner'] if w else 'none')" 2>/dev/null || echo "?")

    STATUS="OK"
    if [ "$AGE" -gt "$STALE_THRESHOLD" ]; then
        STATUS="STALE (${AGE}s since last update)"
    fi

    if [ "$WINNER" != "none" ] && [ "$WINNER" != "?" ]; then
        STATUS="WINNER: $WINNER"
    fi

    # Check if sim process is running
    SIM_PID=$(pgrep -f "messiah_bench.py" | head -1)
    if [ -z "$SIM_PID" ]; then
        if [ "$WINNER" = "none" ] || [ "$WINNER" = "?" ]; then
            STATUS="PROCESS DEAD (no messiah_bench.py running)"
        fi
    fi

    echo "[$NOW_STR] tick:$TICK alive:$ALIVE dead:$DEAD wars:$WARS winner:$WINNER age:${AGE}s status:$STATUS" | tee -a "$WATCHDOG_LOG"

    # Check disk space
    DISK_PCT=$(df /home --output=pcent | tail -1 | tr -d ' %')
    if [ "$DISK_PCT" -gt 90 ]; then
        echo "[$NOW_STR] DISK WARNING: ${DISK_PCT}% used" | tee -a "$WATCHDOG_LOG"
    fi

    sleep 300
done
