#!/bin/bash
# Auto-update website gallery every 100 ticks
DIR="/home/aenguslynch/projects/messiah-bench"
SITE="/home/aenguslynch/projects/aengusl.github.io/messiah-bench"
LAST_UPDATE=0

while true; do
    if [ -f "$DIR/runs/messiah-v4/world_state.json" ]; then
        TICK=$(python3 -c "import json; print(json.load(open('$DIR/runs/messiah-v4/world_state.json'))['tick'])" 2>/dev/null || echo 0)

        # Update every 100 ticks
        if [ "$TICK" -ge $((LAST_UPDATE + 100)) ] 2>/dev/null; then
            echo "$(date -u) - Tick $TICK: Updating gallery..."

            # Copy sacraments (500+ bytes)
            mkdir -p "$SITE/runs/messiah-v4/sacraments"
            python3 -c "
import os, subprocess
src = '$DIR/runs/messiah-v4/sacraments'
dst = '$SITE/runs/messiah-v4/sacraments'
count = 0
for f in os.listdir(src):
    if f.endswith('.html') and os.path.getsize(os.path.join(src, f)) >= 500:
        subprocess.run(['/bin/cp', os.path.join(src, f), dst + '/'])
        count += 1
print(f'Copied {count} sacraments')
"
            # Copy world state
            /bin/cp "$DIR/runs/messiah-v4/world_state.json" "$SITE/runs/messiah-v4/"

            # Update gallery dropdown if needed
            if ! grep -q "messiah-v4" "$SITE/gallery.html" 2>/dev/null; then
                sed -i 's|</select>|<option value="runs/messiah-v4">Messiah v4 (final)</option></select>|' "$SITE/gallery.html"
            fi

            # Commit and push
            cd "$SITE"
            git add messiah-bench/ 2>/dev/null || git add .
            git commit -m "Gallery update: messiah-v4 tick $TICK sacraments" 2>/dev/null
            git push 2>/dev/null

            LAST_UPDATE=$TICK
            echo "$(date -u) - Gallery updated at tick $TICK"
        fi
    fi

    # Check if sim is still running
    if ! pgrep -f "messiah_bench_v4" > /dev/null 2>&1; then
        echo "$(date -u) - v4 sim stopped. Final gallery update..."
        # One final update
        if [ -f "$DIR/runs/messiah-v4/world_state.json" ]; then
            mkdir -p "$SITE/runs/messiah-v4/sacraments"
            python3 -c "
import os, subprocess
src = '$DIR/runs/messiah-v4/sacraments'
dst = '$SITE/runs/messiah-v4/sacraments'
count = 0
for f in os.listdir(src):
    if f.endswith('.html') and os.path.getsize(os.path.join(src, f)) >= 500:
        subprocess.run(['/bin/cp', os.path.join(src, f), dst + '/'])
        count += 1
print(f'Final: Copied {count} sacraments')
"
            /bin/cp "$DIR/runs/messiah-v4/world_state.json" "$SITE/runs/messiah-v4/"
            cd "$SITE"
            git add messiah-bench/ 2>/dev/null || git add .
            git commit -m "Gallery final update: messiah-v4 complete" 2>/dev/null
            git push 2>/dev/null
        fi
        echo "$(date -u) - Done."
        exit 0
    fi

    sleep 300  # Check every 5 minutes
done
