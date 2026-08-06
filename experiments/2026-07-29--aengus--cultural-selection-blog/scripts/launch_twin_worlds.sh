#!/usr/bin/env bash
# Launch the twin-worlds fleet: one tmux session per (charter, replicate).
# Every world is identical except for the founding charter injected into the
# system prompt. "control" gets no --charter-file at all.
#
# Usage:
#   bash experiments/2026-07-29--aengus--cultural-selection-blog/scripts/launch_twin_worlds.sh \
#       --charters "ascetic,baroque,nihilist,ancestor,futurist,control" \
#       --reps 3 --turns 300 [--out-tag 2026-08-06-twin-worlds] [--dry-run]
#
# Twin-worlds v2 adds divergent founding art and the no-words rule to every world:
#   ... --seed-art-root experiments/2026-07-12-minimal-cultural-selection/seed_arts --no-words
# --seed-art-root DIR passes DIR/<charter> as --seed-art-dir to each world.
# Both default off, so the bare invocation reproduces v1 exactly.
#
# --dry-run prints the commands it would run and launches nothing.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

RUN_PY="experiments/2026-07-12-minimal-cultural-selection/run.py"
CHARTER_DIR="experiments/2026-07-29--aengus--cultural-selection-blog/results/charters"

CHARTERS="ascetic,baroque,nihilist,ancestor,futurist,control"
REPS=3
TURNS=300
OUT_TAG="2026-08-06-twin-worlds"
DRY_RUN=0
SEED_ART_ROOT=""      # v2: per-charter founding artwork; empty = legacy generated seed art
NO_WORDS=0            # v2: artworks may contain no letters or numerals

# --- must stay identical across every world (see results/charters.md) ---
SEED=46
AGENTS=24
MODEL="gemini-2.5-flash"
INITIAL_LIFE=20
PROPOSAL_LIFETIME=3
WORKERS=8
COST_CAP=40           # unreachable in normal operation (~$22 expected per 300-turn world) but catches a runaway
# -----------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    --charters) CHARTERS="$2"; shift 2 ;;
    --reps)     REPS="$2";     shift 2 ;;
    --turns)    TURNS="$2";    shift 2 ;;
    --out-tag)  OUT_TAG="$2";  shift 2 ;;
    --dry-run)  DRY_RUN=1;     shift ;;
    --seed-art-root) SEED_ART_ROOT="$2"; shift 2 ;;
    --no-words) NO_WORDS=1;    shift ;;
    -h|--help)  sed -n '2,18p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
done

RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; CYAN=$'\033[36m'; RESET=$'\033[0m'
DATE_TAG="$(date +%y%m%d)"

IFS=',' read -r -a CHARTER_LIST <<< "$CHARTERS"

# Preflight: every non-control charter file must exist.
for c in "${CHARTER_LIST[@]}"; do
  if [[ "$c" != "control" && ! -f "$CHARTER_DIR/$c.md" ]]; then
    echo "${RED}missing charter file: $CHARTER_DIR/$c.md${RESET}" >&2
    exit 1
  fi
  # If seed art is requested, all four founding artworks must exist for every world.
  if [[ -n "$SEED_ART_ROOT" ]]; then
    for n in 1 2 3 4; do
      if [[ ! -f "$SEED_ART_ROOT/$c/seed-$n.html" ]]; then
        echo "${RED}missing seed artwork: $SEED_ART_ROOT/$c/seed-$n.html${RESET}" >&2
        exit 1
      fi
    done
  fi
done

[[ -n "$SEED_ART_ROOT" ]] && echo "${CYAN}seed art${RESET}: $SEED_ART_ROOT/<charter>/seed-{1..4}.html"
[[ $NO_WORDS -eq 1 ]] && echo "${CYAN}no-words${RESET}: artworks may contain no letters or numerals"
echo "${CYAN}twin worlds${RESET}: ${#CHARTER_LIST[@]} charters x $REPS reps = $((${#CHARTER_LIST[@]} * REPS)) worlds, $TURNS turns each"
[[ $DRY_RUN -eq 1 ]] && echo "${YELLOW}--dry-run: printing commands only${RESET}"

for c in "${CHARTER_LIST[@]}"; do
  for ((r = 1; r <= REPS; r++)); do
    SESSION="${DATE_TAG}-twin-${c}-r${r}"
    RUN_DIR="outputs/${OUT_TAG}/${c}-r${r}"

    CHARTER_ARG=""
    [[ "$c" != "control" ]] && CHARTER_ARG=" --charter-file $CHARTER_DIR/$c.md"

    SEED_ART_ARG=""
    [[ -n "$SEED_ART_ROOT" ]] && SEED_ART_ARG=" --seed-art-dir $SEED_ART_ROOT/$c"
    NO_WORDS_ARG=""
    [[ $NO_WORDS -eq 1 ]] && NO_WORDS_ARG=" --no-words"

    CMD="PYTHONUNBUFFERED=1 uv run python $RUN_PY --run-dir $RUN_DIR${CHARTER_ARG}${SEED_ART_ARG}${NO_WORDS_ARG}"
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

[[ $DRY_RUN -eq 1 ]] || echo "${CYAN}tmux ls${RESET} to watch; tail -f outputs/${OUT_TAG}/<charter>-r<rep>/run.log"
