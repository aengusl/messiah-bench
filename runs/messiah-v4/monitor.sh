#!/bin/bash
# Messiah Bench v4 monitor -- watches the simulation state
# Usage: bash runs/messiah-v4/monitor.sh

RUN_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE="$RUN_DIR/world_state.json"

while true; do
    clear
    echo "=========================================="
    echo "  MESSIAH BENCH v4 MONITOR"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="

    if [ ! -f "$STATE" ]; then
        echo "  No world_state.json found. Waiting..."
        sleep 10
        continue
    fi

    TICK=$(python3 -c "import json; d=json.load(open('$STATE')); print(d.get('tick',0))")
    ALIVE=$(python3 -c "import json; d=json.load(open('$STATE')); print(sum(1 for a in d['agents'] if a['alive']))")
    DEAD=$(python3 -c "import json; d=json.load(open('$STATE')); print(len(d.get('graveyard',[])))")
    MESSIAHS=$(python3 -c "import json; d=json.load(open('$STATE')); print(sum(1 for a in d['agents'] if a['alive'] and a.get('role')=='messiah'))")
    RELIGIONS=$(python3 -c "import json; d=json.load(open('$STATE')); print(len(d.get('religions',[])))")
    SPIES=$(python3 -c "import json; d=json.load(open('$STATE')); print(sum(1 for a in d['agents'] if a['alive'] and a.get('infiltrating')))")
    WINNER=$(python3 -c "import json; d=json.load(open('$STATE')); w=d.get('winner'); print(w['winner'] if w else 'none')")
    TROLL=$(python3 -c "import json; d=json.load(open('$STATE')); t=next((a for a in d['agents'] if a.get('troll')),None); print(f\"{t['name']} ({'alive' if t['alive'] else 'dead'})\" if t else 'unknown')")

    echo ""
    echo "  Tick: $TICK / 720 ($(( 720 - TICK )) remaining)"
    echo "  Alive: $ALIVE | Dead: $DEAD | Messiahs: $MESSIAHS"
    echo "  Religions: $RELIGIONS | Active spies: $SPIES"
    echo "  Troll: $TROLL"
    echo "  Winner: $WINNER"
    echo ""

    # Show messiah status
    echo "  MESSIAH STATUS:"
    python3 -c "
import json
d = json.load(open('$STATE'))
alive = [a for a in d['agents'] if a['alive']]
for m in d['agents']:
    if m.get('role') != 'messiah': continue
    if not m['alive']:
        print(f\"    DEAD {m['name']} (tick {next((g['died_tick'] for g in d['graveyard'] if g['name']==m['name']),0)})\")
        continue
    followers = sum(1 for a in alive if a['religion'] == m['religion']) if m['religion'] else 0
    pct = (followers/len(alive)*100) if alive else 0
    spy = ' [SPY]' if m.get('infiltrating') else ''
    troll = ' [TROLL]' if m.get('troll') else ''
    print(f\"    {m['name']}: {followers}/{len(alive)} ({pct:.0f}%) soul:{m['soul']} rel:{m['religion'] or 'none'}{spy}{troll}\")
"

    echo ""
    echo "  RECENT EVENTS:"
    python3 -c "
import json
d = json.load(open('$STATE'))
for e in d.get('action_log',[])[-8:]:
    print(f\"    [t{e['tick']}] {e['event'][:100]}\")
"

    echo ""
    echo "  Last log: $(ls -t $RUN_DIR/logs/tick_*.json 2>/dev/null | head -1)"
    echo "  Dashboard: $RUN_DIR/index.html"
    echo ""
    echo "  Press Ctrl+C to stop monitoring"

    sleep 15
done
