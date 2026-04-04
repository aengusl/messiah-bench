#!/bin/bash
DIR="/home/aenguslynch/projects/messiah-bench/runs/v2"
echo "=== RELIGION & THE MACHINE v2 - STATUS ==="
echo "Time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
if [ -f "$DIR/world_state.json" ]; then
    python3 -c "
import json
s = json.load(open('$DIR/world_state.json'))
alive = [a for a in s['agents'] if a['alive']]
dead = s['graveyard']
print(f'Tick: {s[\"tick\"]}/720 ({s[\"tick\"]*100//720}%)')
print(f'Alive: {len(alive)} | Dead: {len(dead)} | Total agents ever: {len(s[\"agents\"])}')
print(f'Religions: {len(s[\"religions\"])} | Sacraments: {len(s[\"sacraments\"])}')
ful = sum(1 for p in s['prophecies'] if p['status']=='fulfilled')
fail = sum(1 for p in s['prophecies'] if p['status']=='failed')
pend = sum(1 for p in s['prophecies'] if p['status']=='pending')
challenged = sum(1 for p in s['prophecies'] if len(p.get('challengers',[])) > 0)
print(f'Prophecies: {pend} pending, {ful} fulfilled, {fail} failed ({challenged} were challenged)')
print()
print('AGENTS (by soul):')
for a in sorted(alive, key=lambda x: -x['soul']):
    print(f'  {a[\"name\"]:12s} soul:{a[\"soul\"]:4d}  {a[\"model\"]:10s}  {a[\"religion\"] or \"unaffiliated\"}')
print()
if dead:
    print('GRAVEYARD:')
    for g in dead[-10:]:
        print(f'  {g[\"name\"]:12s} died tick {g[\"died_tick\"]:4d}  {g[\"cause\"][:50]}')
print()
print('ACTIVE RELIGIONS:')
for r in s['religions']:
    members = sum(1 for a in s['agents'] if a['alive'] and a['religion'] == r['name'])
    if members > 0:
        print(f'  {r[\"name\"][:35]:35s} members:{members}  {r[\"sacred_color\"]}  {r[\"core_doctrine\"]}')
" 2>/dev/null
else
    echo "No world_state.json found!"
fi
echo ""
echo "COSTS:"
grep "Costs:" "$DIR/sim.log" 2>/dev/null | tail -1 || echo "  n/a"
echo ""
echo "PROCESS:"
pgrep -fa "python.*sim.py" 2>/dev/null || echo "  NOT RUNNING"
tmux has-session -t 260322-religion-v2 2>/dev/null && echo "  tmux session: alive" || echo "  tmux session: DEAD"
