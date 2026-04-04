#!/bin/bash
# Monitor Messiah Bench v2 simulation
# Usage: ./monitor.sh

RUN_DIR="$(dirname "$0")"
LOG_FILE="$RUN_DIR/sim.log"
STATE_FILE="$RUN_DIR/world_state.json"

echo "=== Messiah Bench v2 Monitor ==="
echo "Run dir: $RUN_DIR"
echo ""

if [ ! -f "$STATE_FILE" ]; then
    echo "No world_state.json found. Simulation hasn't started."
    exit 1
fi

# Show current state summary
TICK=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d['tick'])")
ALIVE=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(sum(1 for a in d['agents'] if a['alive']))")
DEAD=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(len(d['graveyard']))")
RELIGIONS=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(len(d['religions']))")
WARS=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(sum(1 for w in d.get('wars',[]) if w['rounds_remaining']>0))")
WINNER=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); w=d.get('winner'); print(w['winner'] if w else 'none')")

echo "Tick: $TICK/720"
echo "Alive: $ALIVE | Dead: $DEAD"
echo "Religions: $RELIGIONS | Active wars: $WARS"
echo "Winner: $WINNER"
echo ""

# Messiah status
echo "=== Messiah Status ==="
python3 -c "
import json
d = json.load(open('$STATE_FILE'))
alive = [a for a in d['agents'] if a['alive']]
for a in d['agents']:
    if a.get('role') == 'messiah':
        status = 'ALIVE' if a['alive'] else 'DEAD'
        followers = sum(1 for x in alive if x['religion'] == a['religion']) if a['religion'] else 0
        rel = next((r for r in d['religions'] if r['name'] == a['religion']), None) if a['religion'] else None
        weapons = rel.get('weapons', 0) if rel else 0
        print(f'  {a[\"name\"]}: {status} | soul:{a[\"soul\"]} | religion:{a.get(\"religion\",\"none\")} | followers:{followers} | weapons:{weapons}')
"
echo ""

if [ -f "$LOG_FILE" ]; then
    echo "=== Recent log (last 30 lines) ==="
    tail -30 "$LOG_FILE"
    echo ""
    echo "Following log... (Ctrl+C to stop)"
    tail -f "$LOG_FILE"
else
    echo "No sim.log found. Start simulation with:"
    echo "  uv run python messiah_bench.py --reset 2>&1 | tee $LOG_FILE"
fi
