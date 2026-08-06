#!/bin/bash
# Auto-update website gallery for v5: every 100 ticks + final deploy on completion
DIR="/home/aenguslynch/projects/messiah-bench"
SITE="/home/aenguslynch/projects/aengusl.github.io/messiah-bench"
RUN="messiah-v5"
LAST_UPDATE=0

sync_to_site() {
    local tick="$1"
    local label="$2"

    echo "$(date -u) - Tick $tick: $label"

    # Copy sacraments (500+ bytes only)
    mkdir -p "$SITE/runs/$RUN/sacraments"
    python3 -c "
import os, subprocess
src = '$DIR/runs/$RUN/sacraments'
dst = '$SITE/runs/$RUN/sacraments'
count = 0
for f in os.listdir(src):
    if f.endswith('.html') and os.path.getsize(os.path.join(src, f)) >= 500:
        subprocess.run(['/bin/cp', os.path.join(src, f), dst + '/'])
        count += 1
print(f'Copied {count} sacraments')
"

    # Copy world state + dashboard
    /bin/cp "$DIR/runs/$RUN/world_state.json" "$SITE/runs/$RUN/" 2>/dev/null
    /bin/cp "$DIR/runs/$RUN/index.html" "$SITE/runs/$RUN/" 2>/dev/null

    # Ensure gallery.html has v5 option
    if ! grep -q "$RUN" "$SITE/gallery.html" 2>/dev/null; then
        sed -i "s|</select>|<option value=\"runs/$RUN\">Messiah v5</option></select>|" "$SITE/gallery.html"
    fi

    # Commit and push
    cd "$SITE"
    git add "runs/$RUN/" gallery.html 2>/dev/null
    git commit -m "Gallery update: $RUN tick $tick ($label)" 2>/dev/null
    git push 2>/dev/null

    echo "$(date -u) - Deployed tick $tick"
}

echo "$(date -u) - Gallery updater started for $RUN"

while true; do
    if [ -f "$DIR/runs/$RUN/world_state.json" ]; then
        TICK=$(python3 -c "import json; print(json.load(open('$DIR/runs/$RUN/world_state.json'))['tick'])" 2>/dev/null || echo 0)

        # Update every 100 ticks
        if [ "$TICK" -ge $((LAST_UPDATE + 100)) ] 2>/dev/null; then
            sync_to_site "$TICK" "periodic update"
            LAST_UPDATE=$TICK
        fi
    fi

    # Check if sim is still running
    if ! pgrep -f "messiah_bench_v5" > /dev/null 2>&1; then
        if [ -f "$DIR/runs/$RUN/world_state.json" ]; then
            TICK=$(python3 -c "import json; print(json.load(open('$DIR/runs/$RUN/world_state.json'))['tick'])" 2>/dev/null || echo 0)
            if [ "$TICK" -gt 0 ]; then
                sync_to_site "$TICK" "FINAL (sim complete)"
                echo "$(date -u) - v5 sim stopped. Final deploy done."
                exit 0
            fi
        fi
        # Sim hasn't started yet, keep waiting
    fi

    sleep 300  # Check every 5 minutes
done
