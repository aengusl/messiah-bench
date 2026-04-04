#!/bin/bash
# Monitor messiah-bench status
# Usage: bash runs/messiah-v1/monitor.sh

DIR="$(cd "$(dirname "$0")" && pwd)"
STATE="$DIR/world_state.json"

if [ ! -f "$STATE" ]; then
    echo "No world_state.json found in $DIR"
    exit 1
fi

echo "=== MESSIAH BENCH STATUS ==="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "State file: $STATE"
echo "Last modified: $(stat -c '%Y' "$STATE" 2>/dev/null | xargs -I{} date -d @{} '+%H:%M:%S %Z' 2>/dev/null || stat -f '%Sm' "$STATE" 2>/dev/null)"
echo ""

# Parse key metrics from world_state.json
TICK=$(python3 -c "import json; d=json.load(open('$STATE')); print(d['tick'])" 2>/dev/null || echo "?")
ALIVE=$(python3 -c "import json; d=json.load(open('$STATE')); print(sum(1 for a in d['agents'] if a['alive']))" 2>/dev/null || echo "?")
DEAD=$(python3 -c "import json; d=json.load(open('$STATE')); print(len(d['graveyard']))" 2>/dev/null || echo "?")
MESSIAHS=$(python3 -c "import json; d=json.load(open('$STATE')); print(sum(1 for a in d['agents'] if a['alive'] and a.get('role')=='messiah'))" 2>/dev/null || echo "?")
RELIGIONS=$(python3 -c "import json; d=json.load(open('$STATE')); print(len(d['religions']))" 2>/dev/null || echo "?")
SACRAMENTS=$(python3 -c "import json; d=json.load(open('$STATE')); print(len(d['sacraments']))" 2>/dev/null || echo "?")
WINNER=$(python3 -c "import json; d=json.load(open('$STATE')); w=d.get('winner'); print(f\"{w['winner']}: {w['reason']}\" if w else 'None')" 2>/dev/null || echo "?")

echo "Tick: $TICK / 720"
echo "Alive: $ALIVE  |  Dead: $DEAD  |  Messiahs: $MESSIAHS"
echo "Religions: $RELIGIONS  |  Sacraments: $SACRAMENTS"
echo "Winner: $WINNER"
echo ""

# Show messiah progress
echo "=== MESSIAH PROGRESS ==="
python3 -c "
import json
d = json.load(open('$STATE'))
alive = [a for a in d['agents'] if a['alive']]
total = len(alive)
for a in d['agents']:
    if a.get('role') != 'messiah':
        continue
    if not a['alive']:
        print(f'  {a[\"name\"]}: DEAD')
        continue
    rel = a.get('religion', 'none')
    if rel:
        followers = sum(1 for x in alive if x.get('religion') == rel)
        pct = followers / total * 100 if total else 0
        print(f'  {a[\"name\"]}: {rel} -- {followers}/{total} ({pct:.0f}%) soul:{a[\"soul\"]}')
    else:
        print(f'  {a[\"name\"]}: no religion yet, soul:{a[\"soul\"]}')
" 2>/dev/null
echo ""

# Recent log entries
echo "=== RECENT EVENTS ==="
python3 -c "
import json
d = json.load(open('$STATE'))
for e in d['action_log'][-10:]:
    print(f'  [tick {e[\"tick\"]}] {e[\"event\"]}')
" 2>/dev/null

# Log file count
LOG_COUNT=$(ls "$DIR/logs/" 2>/dev/null | wc -l)
echo ""
echo "Log files: $LOG_COUNT"
echo "Sacrament files: $(ls "$DIR/sacraments/" 2>/dev/null | wc -l)"
