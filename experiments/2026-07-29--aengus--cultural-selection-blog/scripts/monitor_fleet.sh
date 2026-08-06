#!/bin/bash
# Fleet watchdog: emits one line on completion, crash, or error storm; else silent.
D="${1:-/home/aenguslynch/projects/messiah-bench/.claude/worktrees/2026-07-29-cultural-selection-brainstorm/outputs/2026-08-06-twin-worlds}"
EXPECTED="${2:-18}"
PATTERN="${3:-twin}"
while true; do
  done_n=$(find "$D" -name COMPLETE 2>/dev/null | wc -l)
  alive=$(tmux ls 2>/dev/null | grep -c "$PATTERN")
  errs=$(tail -qn1 "$D"/*/run.log 2>/dev/null | grep -oE '"errors": [0-9]+' | awk '{s+=$2} END{print s+0}')
  cost=$(tail -qn1 "$D"/*/run.log 2>/dev/null | grep -oE '"estimated_cost": [0-9.]+' | awk '{s+=$2} END{printf "%.0f", s}')
  if [ "$done_n" -ge "$EXPECTED" ]; then
    echo "FLEET COMPLETE: $done_n/$EXPECTED worlds, errs=$errs cost=\$$cost"; exit 0
  fi
  if [ "$alive" -eq 0 ]; then
    echo "FLEET DEAD: tmux gone with $done_n/$EXPECTED complete, errs=$errs cost=\$$cost"; exit 1
  fi
  if [ "$errs" -gt 2000 ]; then
    echo "FLEET ERROR STORM: errs=$errs done=$done_n alive=$alive cost=\$$cost"; exit 1
  fi
  sleep 300
done
