#!/bin/bash
# Monitor messiah-bench v3 run
# Usage: bash monitor.sh

RUN_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_FILE="$RUN_DIR/world_state.json"

while true; do
    clear
    echo "=== MESSIAH BENCH v3 MONITOR ==="
    echo "$(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    if [ ! -f "$STATE_FILE" ]; then
        echo "No state file found. Waiting..."
        sleep 10
        continue
    fi

    # Current tick
    TICK=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(d['tick'])")
    ALIVE=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(sum(1 for a in d['agents'] if a['alive']))")
    DEAD=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(len(d['graveyard']))")
    RELIGIONS=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(len(d['religions']))")
    SACRAMENTS=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(len(d['sacraments']))")
    MESSIAHS=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); print(sum(1 for a in d['agents'] if a['alive'] and a.get('role')=='messiah'))")
    WINNER=$(python3 -c "import json; d=json.load(open('$STATE_FILE')); w=d.get('winner'); print(w['winner'] if w else 'none')")

    echo "Tick: $TICK/720"
    echo "Alive: $ALIVE ($MESSIAHS messiahs)"
    echo "Dead: $DEAD"
    echo "Religions: $RELIGIONS"
    echo "Sacraments: $SACRAMENTS"
    echo "Winner: $WINNER"
    echo ""

    # Messiah progress
    echo "--- Messiah Progress ---"
    python3 -c "
import json
d = json.load(open('$STATE_FILE'))
alive = [a for a in d['agents'] if a['alive']]
total = len(alive)
for a in d['agents']:
    if a.get('role') == 'messiah':
        if a['alive']:
            fol = sum(1 for x in alive if x['religion'] == a['religion']) if a['religion'] else 0
            pct = fol/total*100 if total else 0
            print(f\"  {a['name']}: {fol}/{total} ({pct:.0f}%) soul:{a['soul']} rel:{a['religion'] or 'none'}\")
        else:
            print(f\"  {a['name']}: DEAD\")
"
    echo ""

    # Sacrament versions
    echo "--- Sacraments ---"
    python3 -c "
import json
d = json.load(open('$STATE_FILE'))
for s in d['sacraments']:
    editors = len(s.get('edit_log', []))
    print(f\"  {s['religion']}: v{s['version']} ({editors} edits) - {s['title'][:50]}\")
" 2>/dev/null || echo "  (none)"
    echo ""

    # Recent events
    echo "--- Recent Events ---"
    python3 -c "
import json
d = json.load(open('$STATE_FILE'))
for e in d.get('action_log', [])[-8:]:
    print(f\"  [t{e['tick']}] {e['event'][:100]}\")
"
    echo ""

    # Disk usage
    echo "--- Disk ---"
    du -sh "$RUN_DIR" 2>/dev/null
    echo "Sacrament files: $(ls "$RUN_DIR/sacraments/" 2>/dev/null | wc -l)"
    echo "Log files: $(ls "$RUN_DIR/logs/" 2>/dev/null | wc -l)"

    sleep 15
done
