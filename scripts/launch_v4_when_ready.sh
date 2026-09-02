#!/bin/bash
# Wait for v3 to finish, then launch v4
DIR="/home/aenguslynch/projects/messiah-bench"

while true; do
    # Check if v3 sim process is still running
    if ! pgrep -f "messiah_bench.py.*messiah-v3" > /dev/null 2>&1; then
        echo "$(date -u) - v3 process stopped, launching v4..."
        
        # Clean v4 run dir
        find $DIR/runs/messiah-v4/sacraments -type f -exec /bin/rm {} + 2>/dev/null
        find $DIR/runs/messiah-v4/logs -type f -exec /bin/rm {} + 2>/dev/null
        /bin/rm -f $DIR/runs/messiah-v4/world_state.json $DIR/runs/messiah-v4/index.html $DIR/runs/messiah-v4/sim.log
        
        # Launch v4
        tmux new-session -d -s 260404-messiah-v4 "PYTHONUNBUFFERED=1 uv run python $DIR/src/messiah_bench_v4.py --run-dir=$DIR/runs/messiah-v4 2>&1 | tee $DIR/runs/messiah-v4/sim.log"
        echo "$(date -u) - v4 launched in tmux 260404-messiah-v4"
        exit 0
    fi
    
    # Check v3 tick
    TICK=$(python3 -c "import json; print(json.load(open('$DIR/runs/messiah-v3/world_state.json'))['tick'])" 2>/dev/null || echo "?")
    echo "$(date -u) - v3 still running at tick $TICK/720"
    sleep 120
done
