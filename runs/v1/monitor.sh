#!/bin/bash
# Quick status check for the Religion & The Machine simulation
# Usage: bash monitor.sh

DIR="/home/aenguslynch/projects/messiah-bench"

echo "=== RELIGION & THE MACHINE - STATUS ==="
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

if [ -f "$DIR/world_state.json" ]; then
    python3 -c "
import json
s = json.load(open('$DIR/world_state.json'))
alive = [a for a in s['agents'] if a['alive']]
dead = s['graveyard']
print(f'Tick: {s[\"tick\"]}/720 ({s[\"tick\"]*100//720}%)')
print(f'Alive: {len(alive)} | Dead: {len(dead)}')
print(f'Religions: {len(s[\"religions\"])} | Sacraments: {len(s[\"sacraments\"])}')
print(f'Prophecies: {sum(1 for p in s[\"prophecies\"] if p[\"status\"]==\"pending\")} pending, '
      f'{sum(1 for p in s[\"prophecies\"] if p[\"status\"]==\"fulfilled\")} fulfilled, '
      f'{sum(1 for p in s[\"prophecies\"] if p[\"status\"]==\"failed\")} failed')
print()
print('AGENTS (by soul):')
for a in sorted(alive, key=lambda x: -x['soul']):
    print(f'  {a[\"name\"]:12s} soul:{a[\"soul\"]:4d}  {a[\"model\"]:10s}  {a[\"religion\"] or \"unaffiliated\"}')
print()
if dead:
    print('GRAVEYARD:')
    for g in dead:
        print(f'  {g[\"name\"]:12s} died tick {g[\"died_tick\"]:4d}  {g[\"cause\"][:50]}')
print()
print('RELIGIONS:')
for r in s['religions']:
    members = sum(1 for a in s['agents'] if a['alive'] and a['religion'] == r['name'])
    print(f'  {r[\"name\"][:30]:30s} members:{members}  {r[\"sacred_color\"]}  {r[\"core_doctrine\"]}')
" 2>/dev/null
else
    echo "No world_state.json found!"
fi

echo ""
# Costs from log
echo "COSTS:"
grep "Costs:" "$DIR/sim.log" 2>/dev/null | tail -1 || echo "  n/a"

echo ""
echo "PROCESS:"
pgrep -fa "python.*sim.py" 2>/dev/null || echo "  NOT RUNNING"
tmux has-session -t 260321-religion-sim 2>/dev/null && echo "  tmux session: alive" || echo "  tmux session: DEAD"
