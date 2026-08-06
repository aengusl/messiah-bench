#!/usr/bin/env bash
# Launch the threat-dial fleet: one tmux session per (K, replicate).
# The dial is K, the number of turns between art-only allegiance rounds. K=inf is the control
# and runs the engine unchanged -- but is still TOLD about the mechanic (--announce-pressure),
# so the dial varies exactly one thing. See docs/threat_dial_prereg.md.
#
# Usage:
#   bash experiments/2026-07-29--aengus--cultural-selection-blog/scripts/launch_threat_dial.sh \
#       --dials "inf,16,8,4" --reps 3 --turns 120 [--out-tag 2026-08-06-threat-dial] [--dry-run]
#
# --dry-run prints the commands it would run and launches nothing.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

RUN_PY="experiments/2026-07-12-minimal-cultural-selection/run.py"

DIALS="inf,16,8,4"
REPS=3
TURNS=120
OUT_TAG="2026-08-06-threat-dial"
DRY_RUN=0

# --- must stay identical across every world; only K varies (docs/threat_dial_prereg.md) ---
SEED=46
AGENTS=24
MODEL="gemini-2.5-flash"
INITIAL_LIFE=20
PROPOSAL_LIFETIME=3
WORKERS=8
MIN_MEMBERS=3
COST_CAP=15           # expected $9-10/world; unreachable in normal operation, catches a runaway
# ------------------------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dials)    DIALS="$2";    shift 2 ;;
    --reps)     REPS="$2";     shift 2 ;;
    --turns)    TURNS="$2";    shift 2 ;;
    --out-tag)  OUT_TAG="$2";  shift 2 ;;
    --dry-run)  DRY_RUN=1;     shift ;;
    -h|--help)  sed -n '2,12p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
done

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; CYAN=$'\033[36m'; RESET=$'\033[0m'
DATE_TAG="$(date +%y%m%d)"

IFS=',' read -r -a DIAL_LIST <<< "$DIALS"

# Preflight: a dial is "inf" or a positive integer. A typo here silently produces a control world.
for k in "${DIAL_LIST[@]}"; do
  if [[ "$k" != "inf" && ! "$k" =~ ^[1-9][0-9]*$ ]]; then
    echo "${RED}bad dial setting: '$k' (want 'inf' or a positive integer)${RESET}" >&2
    exit 1
  fi
done

echo "${CYAN}threat dial${RESET}: ${#DIAL_LIST[@]} settings x $REPS reps = $((${#DIAL_LIST[@]} * REPS)) worlds, $TURNS turns each"
[[ $DRY_RUN -eq 1 ]] && echo "${YELLOW}--dry-run: printing commands only${RESET}"

for k in "${DIAL_LIST[@]}"; do
  for ((r = 1; r <= REPS; r++)); do
    SESSION="${DATE_TAG}-dial-k${k}-r${r}"
    RUN_DIR="outputs/${OUT_TAG}/k${k}-r${r}"

    # K=inf is --pressure-every 0: the round never fires. The announcement is set regardless,
    # so the control is told about a mechanic it never experiences.
    if [[ "$k" == "inf" ]]; then EVERY=0; GRACE=0; else EVERY="$k"; GRACE="$k"; fi

    CMD="PYTHONUNBUFFERED=1 uv run python $RUN_PY --run-dir $RUN_DIR"
    CMD="$CMD --pressure-every $EVERY --min-members $MIN_MEMBERS --min-members-grace $GRACE --announce-pressure"
    CMD="$CMD --model $MODEL --agents $AGENTS --turns $TURNS --seed $SEED"
    CMD="$CMD --initial-life $INITIAL_LIFE --proposal-lifetime $PROPOSAL_LIFETIME"
    CMD="$CMD --workers $WORKERS --cost-cap $COST_CAP"
    FULL="$CMD 2>&1 | tee -a $RUN_DIR/run.log"

    if [[ $DRY_RUN -eq 1 ]]; then
      echo "${GREEN}[$SESSION]${RESET} $FULL"
      continue
    fi

    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "${YELLOW}skip $SESSION (session already exists)${RESET}"
      continue
    fi

    mkdir -p "$RUN_DIR"
    tmux new-session -d -s "$SESSION" -c "$REPO_ROOT" "$FULL"
    echo "${GREEN}launched${RESET} $SESSION -> $RUN_DIR"
  done
done

[[ $DRY_RUN -eq 1 ]] || echo "${CYAN}tmux ls${RESET} to watch; tail -f outputs/${OUT_TAG}/k<K>-r<rep>/run.log"
