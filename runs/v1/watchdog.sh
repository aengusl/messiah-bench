#!/bin/bash
# Watchdog for Religion & The Machine simulation
# Checks every 10 minutes: is the sim alive? Is it making progress?

DIR="/home/aenguslynch/projects/messiah-bench"
WATCHDOG_LOG="$DIR/WATCHDOG.md"
TMUX_SESSION="260321-religion-sim"

echo "# Watchdog Log" > "$WATCHDOG_LOG"
echo "Started: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "$WATCHDOG_LOG"
echo "" >> "$WATCHDOG_LOG"

prev_tick=0
stuck_count=0

while true; do
    now=$(date -u '+%Y-%m-%d %H:%M:%S UTC')

    # Get current tick from world_state.json
    if [ -f "$DIR/world_state.json" ]; then
        current_tick=$(python3 -c "import json; print(json.load(open('$DIR/world_state.json'))['tick'])" 2>/dev/null || echo 0)
        alive=$(python3 -c "import json; s=json.load(open('$DIR/world_state.json')); print(sum(1 for a in s['agents'] if a['alive']))" 2>/dev/null || echo "?")
        religions=$(python3 -c "import json; print(len(json.load(open('$DIR/world_state.json'))['religions']))" 2>/dev/null || echo "?")
        sacraments=$(python3 -c "import json; print(len(json.load(open('$DIR/world_state.json'))['sacraments']))" 2>/dev/null || echo "?")
        dead=$(python3 -c "import json; print(len(json.load(open('$DIR/world_state.json'))['graveyard']))" 2>/dev/null || echo "?")
    else
        current_tick=0
        alive="?"
        religions="?"
        sacraments="?"
        dead="?"
    fi

    # Count output files
    sacrament_files=$(find "$DIR/sacraments" -name '*.html' 2>/dev/null | wc -l)
    log_files=$(find "$DIR/logs" -name '*.json' 2>/dev/null | wc -l)

    # Check if tmux session is alive
    tmux_alive=$(tmux has-session -t "$TMUX_SESSION" 2>/dev/null && echo "yes" || echo "NO")

    # Check if sim process is running
    sim_pid=$(pgrep -f "python.*sim.py" 2>/dev/null | head -1)
    sim_alive="no"
    [ -n "$sim_pid" ] && sim_alive="yes (PID $sim_pid)"

    # Get cost from last log line mentioning costs
    cost_line=$(grep "Costs:" "$DIR/sim.log" 2>/dev/null | tail -1 || echo "n/a")

    # Stuck detection
    if [ "$current_tick" = "$prev_tick" ] && [ "$current_tick" != "0" ]; then
        stuck_count=$((stuck_count + 1))
    else
        stuck_count=0
    fi

    # Log entry
    entry="## $now
- Tick: $current_tick/720 | Alive: $alive | Dead: $dead
- Religions: $religions | Sacraments: $sacraments (files: $sacrament_files)
- Log files: $log_files | Tmux: $tmux_alive | Process: $sim_alive
- $cost_line
"

    if [ "$stuck_count" -ge 3 ]; then
        entry="$entry- **ALERT: STUCK for $((stuck_count * 10)) minutes!**
"
    fi

    # Check completion
    if [ "$current_tick" = "720" ] || ([ "$alive" = "0" ] && [ "$current_tick" != "0" ]); then
        entry="$entry- **SIMULATION COMPLETE** (tick $current_tick, $alive alive)
"
        echo "$entry" >> "$WATCHDOG_LOG"
        # Update STATUS.md
        echo "- $now: SIMULATION COMPLETE at tick $current_tick ($alive alive, $dead dead, $sacraments sacraments)" >> "$DIR/STATUS.md"
        exit 0
    fi

    echo "$entry" >> "$WATCHDOG_LOG"
    prev_tick=$current_tick

    # Sleep 10 minutes
    sleep 600
done
