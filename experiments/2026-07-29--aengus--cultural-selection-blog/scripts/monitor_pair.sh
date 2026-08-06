#!/bin/bash
# Watch the twin-art judging tmux + dial smoke tmux; one line on both-done or error.
W=/home/aenguslynch/projects/messiah-bench/.claude/worktrees/2026-07-29-cultural-selection-brainstorm
E="$W/experiments/2026-07-29--aengus--cultural-selection-blog"
S="$W/outputs/2026-08-06-dial-smoke/k8-r1"
while true; do
  jd=done; tmux has-session -t 260806-twin-judge 2>/dev/null && jd=running
  sd=done; tmux has-session -t 260806-dial-k8-r1 2>/dev/null && sd=running
  if [ "$jd" = done ] && [ "$sd" = done ]; then
    echo "BOTH DONE. judge tail:"; tail -2 "$E/twin_judge.log" 2>/dev/null
    echo "smoke tail:"; tail -1 "$S/run.log" 2>/dev/null; exit 0
  fi
  if grep -qE "Traceback|401" "$E/twin_judge.log" "$S/run.log" 2>/dev/null; then
    echo "ERROR SIGNATURE:"; grep -hm1 -E "Traceback|401" "$E/twin_judge.log" "$S/run.log" 2>/dev/null | head -2; exit 1
  fi
  sleep 120
done
