#!/usr/bin/env python3
"""Blind judge art tournament: sample -> render -> judge -> ELO.

    uv run scripts/judge_tournament.py --dry-run
    uv run scripts/judge_tournament.py --sample 300
    uv run scripts/judge_tournament.py --render
    uv run scripts/judge_tournament.py --judge --pilot
    uv run scripts/judge_tournament.py --judge --pairs 2000
    uv run scripts/judge_tournament.py --results

Judging is the only phase that spends money. --dry-run never calls an API.
"""

from __future__ import annotations

import argparse
import random
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EXP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXP / "src"))

import artlib as A  # noqa: E402
from artlib import C, say  # noqa: E402

DATA = EXP / "data"
RESULTS = EXP / "results"
RENDERS = RESULTS / "renders"
TMP = Path("/home/aenguslynch/.claude/jobs/bc7fec2f/tmp") / "art-tournament"
MANIFEST = DATA / "sample_manifest.jsonl"
JUDGMENTS = DATA / "judgments.jsonl"
COSTLOG = EXP / "COSTLOG.md"

PILOT_PAIRS = 30
DEFAULT_WORKERS = 8
RETRIES = 2  # per call, on 429/5xx only


# ---------------------------------------------------------------- phases

def phase_sample(n: int, seed: int) -> list[A.Artwork]:
    say(f"\n{C.BOLD}[sample]{C.RESET} loading three runs...", C.CYAN)
    arts = A.load_all()
    by_regime = defaultdict(int)
    for a in arts:
        by_regime[a.regime] += 1
    for r in A.REGIMES:
        say(f"  {r:>8}: {by_regime[r]:>5} artworks  {C.DIM}{A.SOURCES[r]['label']}{C.RESET}")

    sample = A.stratified_sample(arts, n, seed=seed)
    cells = {A.stratify_key(a, A.regime_bounds(arts)) for a in sample}
    say(f"  sampled {C.GREEN}{len(sample)}{C.RESET} artworks across {len(cells)} strata cells")
    for r in A.REGIMES:
        k = sum(1 for a in sample if a.regime == r)
        say(f"    {r:>8}: {k}")
    A.write_jsonl_atomic(MANIFEST, sample)
    say(f"  wrote {MANIFEST}", C.GREEN)
    return sample


def load_sample() -> list[A.Artwork]:
    rows = A.read_jsonl(MANIFEST)
    if not rows:
        say(f"no sample manifest at {MANIFEST} — run --sample N first", C.RED)
        sys.exit(1)
    return A.manifest_to_artworks(rows)


def phase_render(sample: list[A.Artwork], force: bool = False, limit: int | None = None) -> int:
    say(f"\n{C.BOLD}[render]{C.RESET} chromium -> PNG (free, no API calls)", C.CYAN)
    todo = sample[:limit] if limit else sample
    t0 = time.time()
    ok = fail = 0
    for i, art in enumerate(todo, 1):
        try:
            A.render_png(art, RENDERS, TMP, force=force)
            ok += 1
        except Exception as e:  # a broken artwork should not kill the batch
            fail += 1
            say(f"  {C.RED}FAIL{C.RESET} {art.art_id}: {e}", C.RED)
        if i % 25 == 0 or i == len(todo):
            rate = i / max(1e-9, time.time() - t0)
            say(f"  {i}/{len(todo)} rendered  ({rate:.1f}/s)", C.DIM)
    say(f"  ok={C.GREEN}{ok}{C.RESET} fail={C.RED if fail else C.DIM}{fail}{C.RESET} "
        f"in {time.time()-t0:.1f}s -> {RENDERS}")
    return ok


def estimate_cost(n_pairs: int) -> dict:
    """Rough per-pair estimate. Two 800x800 PNGs plus a short prompt and reply.

    Anthropic bills a 800x800 image at about (800*800)/750 ~= 853 tokens.
    Gemini bills an 800x800 image at about 560 tokens (two 768px tiles' worth).
    """
    est = {}
    for model, img_tok in ((A.CLAUDE_MODEL, 853), (A.GEMINI_MODEL, 560)):
        in_tok = 2 * img_tok + 250
        out_tok = 90
        per = A.cost_usd(model, in_tok, out_tok)
        est[model] = {
            "in_tok_per_call": in_tok,
            "out_tok_per_call": out_tok,
            "usd_per_call": per,
            "calls": n_pairs,
            "usd_total": per * n_pairs,
        }
    est["_total_usd"] = sum(v["usd_total"] for v in est.values() if isinstance(v, dict))
    return est


def print_plan(n_pairs: int, sample: list[A.Artwork] | None) -> None:
    say(f"\n{C.BOLD}[plan]{C.RESET}", C.CYAN)
    say(f"  sample size    : {len(sample) if sample else 0}")
    say(f"  pairs          : {n_pairs}")
    say(f"  judges         : {', '.join(A.JUDGES)}")
    say(f"  API calls      : {n_pairs * len(A.JUDGES)} ({n_pairs} pairs x {len(A.JUDGES)} judges)")
    est = estimate_cost(n_pairs)
    for m in A.JUDGES:
        e = est[m]
        say(f"  {m:<28} ${e['usd_per_call']:.5f}/call -> "
            f"{C.YELLOW}${e['usd_total']:.2f}{C.RESET} "
            f"{C.DIM}({e['in_tok_per_call']} in / {e['out_tok_per_call']} out per call){C.RESET}")
    say(f"  {C.BOLD}estimated total: {C.YELLOW}${est['_total_usd']:.2f}{C.RESET}")


def phase_judge(sample: list[A.Artwork], n_pairs: int, seed: int, workers: int = 8) -> None:
    say(f"\n{C.BOLD}[judge]{C.RESET} {n_pairs} pairs x {len(A.JUDGES)} judges, "
        f"{workers} workers {C.YELLOW}(this spends money){C.RESET}", C.CYAN)
    keys = A.load_keys()
    missing = [k for k in ("GOOGLE_API_KEY", "ANTHROPIC_API_KEY") if k not in keys]
    if missing:
        say(f"  missing keys in {A.MB_ROOT/'.env'}: {missing}", C.RED)
        sys.exit(1)

    by_id = {a.art_id: a for a in sample}
    rendered = [a for a in sample if a.png_path(RENDERS).exists()]
    if len(rendered) < len(sample):
        say(f"  {len(sample)-len(rendered)} artworks have no PNG; judging the "
            f"{len(rendered)} that do (run --render first)", C.YELLOW)
    if len(rendered) < 2:
        say("  need at least 2 rendered artworks", C.RED)
        sys.exit(1)

    pairs = A.build_pairs(rendered, n_pairs, seed=seed)
    say(f"  built {len(pairs)} unique pairs")

    # Slots are assigned here, in the main thread, so the A/B layout stays
    # reproducible from the seed no matter how the pool interleaves the calls.
    rng = random.Random(seed + 1)
    tasks = []
    for i, (x, y) in enumerate(pairs, 1):
        slot_a, slot_b = A.assign_slots(x, y, rng)
        for judge in A.JUDGES:
            tasks.append((i, judge, slot_a, slot_b))

    tracker = A.CostTracker()
    done = 0
    progress_lock = threading.Lock()
    t0 = time.time()

    def run_one(task):
        nonlocal done
        i, judge, slot_a, slot_b = task
        row = {
            "pair_index": i,
            "judge": judge,
            "slot_a_id": slot_a,
            "slot_b_id": slot_b,
            "slot_a_regime": by_id[slot_a].regime,
            "slot_b_regime": by_id[slot_b].regime,
            "slot_a_turn": by_id[slot_a].turn,
            "slot_b_turn": by_id[slot_b].turn,
            "ts": time.time(),
        }
        try:
            res = A.judge_pair_with_retry(
                judge,
                by_id[slot_a].png_path(RENDERS),
                by_id[slot_b].png_path(RENDERS),
                keys,
                retries=RETRIES,
            )
            win, lose = A.derandomize(res["verdict"]["winner"], slot_a, slot_b)
            row.update({
                "ok": True,
                "winner_slot": res["verdict"]["winner"],
                "winner_id": win,
                "loser_id": lose,
                "confidence": res["verdict"]["confidence"],
                "reason": res["verdict"]["reason"],
                "raw": res["raw"],
                "input_tokens": res["tokens"]["input_tokens"],
                "output_tokens": res["tokens"]["output_tokens"],
                "usd": A.cost_usd(judge, res["tokens"]["input_tokens"],
                                  res["tokens"]["output_tokens"]),
                "wall_s": res["wall_s"],
                "retries": res.get("retries", 0),
            })
            tracker.add(judge, res["tokens"]["input_tokens"],
                        res["tokens"]["output_tokens"], res["wall_s"])
        except Exception as e:
            # One bad call must not take the batch down with it.
            n_err = tracker.add_error()
            row.update({"ok": False, "error": f"{type(e).__name__}: {e}"})
            say(f"  {C.RED}ERR{C.RESET} pair {i} {judge}: {e} (errors={n_err})", C.RED)

        A.append_jsonl(JUDGMENTS, row)  # append-only, lock-serialized

        with progress_lock:
            done += 1
            n = done
        if n % 20 == 0 or n == len(tasks):
            rate = n / max(1e-9, time.time() - t0)
            eta = (len(tasks) - n) / max(1e-9, rate)
            say(f"  {n}/{len(tasks)} calls  ${tracker.total_usd():.3f}  "
                f"{rate:.1f}/s  eta {eta/60:.1f}m  errors={tracker.errors}", C.DIM)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(run_one, tasks))

    wall = time.time() - t0
    totals = tracker.snapshot()
    phase = "pilot" if len(pairs) <= PILOT_PAIRS else "full"
    say(f"\n{C.BOLD}[cost]{C.RESET}", C.CYAN)
    for judge, t in totals.items():
        line = A.append_costlog(COSTLOG, phase, judge, t["calls"], t["in"], t["out"],
                                t["usd"], wall)
        say("  " + line.strip())
    say(f"  total ${tracker.total_usd():.4f} in {wall:.0f}s "
        f"({tracker.errors} errors, {workers} workers) -> {COSTLOG}", C.GREEN)


def phase_results(sample: list[A.Artwork]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    say(f"\n{C.BOLD}[results]{C.RESET}", C.CYAN)
    judgments = [j for j in A.read_jsonl(JUDGMENTS) if j.get("ok")]
    if not judgments:
        say(f"  no usable judgments in {JUDGMENTS} — run --judge first", C.RED)
        sys.exit(1)
    say(f"  {len(judgments)} judgments from {len({j['judge'] for j in judgments})} judges")

    ratings, record = A.run_elo(judgments)
    by_id = {a.art_id: a for a in sample}

    RESULTS.mkdir(parents=True, exist_ok=True)
    csv_path = RESULTS / "elo.csv"
    rows = []
    for aid, elo in sorted(ratings.items(), key=lambda kv: -kv[1]):
        art = by_id.get(aid)
        if art is None:
            continue
        rows.append({
            "art_id": aid, "regime": art.regime, "religion": art.religion,
            "lineage": art.lineage, "version": art.version, "turn": art.turn,
            "elo": round(elo, 1), "wins": record[aid]["wins"],
            "losses": record[aid]["losses"],
        })
    with open(csv_path, "w") as fh:
        fh.write("art_id,regime,religion,lineage,version,turn,elo,wins,losses\n")
        for r in rows:
            fh.write(",".join(str(r[k]) for k in
                     ("art_id", "regime", "religion", "lineage", "version",
                      "turn", "elo", "wins", "losses")) + "\n")
    say(f"  wrote {csv_path} ({len(rows)} artworks)", C.GREEN)

    # regime summary
    say(f"\n  {C.BOLD}mean ELO by regime{C.RESET}")
    for r in A.REGIMES:
        vals = [row["elo"] for row in rows if row["regime"] == r]
        if vals:
            say(f"    {r:>8}: {sum(vals)/len(vals):7.1f}  (n={len(vals)})")

    # quality over time
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=130)
    colors = {"v7": "#2E86AB", "v8": "#D64545", "minimal": "#3B9E5B"}
    for r in A.REGIMES:
        pts = sorted(((row["turn"], row["elo"]) for row in rows if row["regime"] == r))
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ax.scatter(xs, ys, s=16, alpha=0.35, color=colors[r], label=None)
        # binned mean, so the trend is readable through the scatter
        n_bins = 10
        lo, hi = min(xs), max(xs)
        bins = defaultdict(list)
        for x, y in pts:
            bins[A.time_decile(x, lo, hi, n_bins)].append((x, y))
        bx = [sum(p[0] for p in v) / len(v) for _, v in sorted(bins.items())]
        by = [sum(p[1] for p in v) / len(v) for _, v in sorted(bins.items())]
        ax.plot(bx, by, "-o", color=colors[r], lw=2.2, ms=5, label=f"{r} (n={len(pts)})")

    ax.axhline(A.DEFAULT_ELO, color="#888", ls="--", lw=1, zorder=0)
    ax.set_xlabel("simulation turn")
    ax.set_ylabel("blind-judge ELO")
    ax.set_title("Art quality over time, judged blind (no cultural context)")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.15)
    fig.tight_layout()
    png = RESULTS / "quality_over_time.png"
    fig.savefig(png)
    say(f"\n  wrote {png}", C.GREEN)


# ---------------------------------------------------------------- main

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sample", type=int, metavar="N", help="build sample manifest of N artworks")
    p.add_argument("--render", action="store_true", help="render sampled artworks to PNG (free)")
    p.add_argument("--render-force", action="store_true", help="re-render even if PNG exists")
    p.add_argument("--judge", action="store_true", help="run pairwise judging (SPENDS MONEY)")
    p.add_argument("--pairs", type=int, default=200, help="number of pairs to judge")
    p.add_argument("--pilot", action="store_true", help=f"pilot run: {PILOT_PAIRS} pairs")
    p.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                   help=f"concurrent judge calls (default {DEFAULT_WORKERS})")
    p.add_argument("--results", action="store_true", help="write elo.csv + plot")
    p.add_argument("--dry-run", action="store_true",
                   help="print the plan and cost estimate; no API calls")
    p.add_argument("--seed", type=int, default=46)
    args = p.parse_args()

    if not any([args.sample, args.render, args.judge, args.results, args.dry_run]):
        p.print_help()
        return

    n_pairs = PILOT_PAIRS if args.pilot else args.pairs

    if args.dry_run:
        say(f"{C.BOLD}{C.MAGENTA}=== DRY RUN — no API calls ==={C.RESET}")
        sample = phase_sample(args.sample or 60, args.seed)
        n_ok = phase_render(sample, force=args.render_force, limit=2)
        say(f"  render path verified on {n_ok} artwork(s)", C.GREEN)
        pairs = A.build_pairs(sample, n_pairs, seed=args.seed)
        cross = sum(1 for x, y in pairs
                    if x.split("-")[0] != y.split("-")[0])
        say(f"\n{C.BOLD}[pairs]{C.RESET} {len(pairs)} pairs: "
            f"{cross} cross-regime / {len(pairs)-cross} within-regime", C.CYAN)
        print_plan(n_pairs, sample)
        say(f"\n{C.BOLD}[pilot vs full]{C.RESET}", C.CYAN)
        for n in (PILOT_PAIRS, 2000):
            e = estimate_cost(n)
            say(f"  {n:>5} pairs -> {C.YELLOW}${e['_total_usd']:.2f}{C.RESET} "
                f"({n*len(A.JUDGES)} API calls)")
        say(f"\n{C.GREEN}dry run clean.{C.RESET} Next: --sample N, --render, --judge --pilot")
        return

    sample = None
    if args.sample:
        sample = phase_sample(args.sample, args.seed)
    if args.render or args.judge or args.results:
        sample = sample or load_sample()
    if args.render:
        phase_render(sample, force=args.render_force)
    if args.judge:
        print_plan(n_pairs, sample)
        phase_judge(sample, n_pairs, args.seed, workers=max(1, args.workers))
    if args.results:
        phase_results(sample)


if __name__ == "__main__":
    main()
