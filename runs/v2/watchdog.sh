#!/bin/bash
DIR="/home/aenguslynch/projects/messiah-bench/runs/v2"
WATCHDOG_LOG="$DIR/WATCHDOG.md"
TMUX_SESSION="260322-religion-v2"

echo "# V2 Watchdog Log" > "$WATCHDOG_LOG"
echo "Started: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "$WATCHDOG_LOG"
echo "" >> "$WATCHDOG_LOG"

prev_tick=0
stuck_count=0

while true; do
    now=$(date -u '+%Y-%m-%d %H:%M:%S UTC')
    if [ -f "$DIR/world_state.json" ]; then
        current_tick=$(python3 -c "import json; print(json.load(open('$DIR/world_state.json'))['tick'])" 2>/dev/null || echo 0)
        alive=$(python3 -c "import json; s=json.load(open('$DIR/world_state.json')); print(sum(1 for a in s['agents'] if a['alive']))" 2>/dev/null || echo "?")
        dead=$(python3 -c "import json; print(len(json.load(open('$DIR/world_state.json'))['graveyard']))" 2>/dev/null || echo "?")
    else
        current_tick=0; alive="?"; dead="?"
    fi

    tmux_alive=$(tmux has-session -t "$TMUX_SESSION" 2>/dev/null && echo "yes" || echo "NO")
    sim_pid=$(pgrep -f "python.*sim.py" 2>/dev/null | head -1)

    if [ "$current_tick" = "$prev_tick" ] && [ "$current_tick" != "0" ]; then
        stuck_count=$((stuck_count + 1))
    else
        stuck_count=0
    fi

    entry="## $now
- Tick: $current_tick/720 | Alive: $alive | Dead: $dead | Tmux: $tmux_alive
"
    [ "$stuck_count" -ge 3 ] && entry="$entry- **STUCK for $((stuck_count * 10))min!**
"

    if [ "$current_tick" = "720" ] || ([ "$alive" = "0" ] && [ "$current_tick" != "0" ]); then
        entry="$entry- **COMPLETE** at tick $current_tick
"
        echo "$entry" >> "$WATCHDOG_LOG"
        exit 0
    fi

    echo "$entry" >> "$WATCHDOG_LOG"
    prev_tick=$current_tick
    sleep 600
done
