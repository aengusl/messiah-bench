#!/usr/bin/env python3
"""
Messiah-Bench cross-sim analysis.

Reads every runs/messiah-v{1..6}/world_state.json, computes hypothesis-relevant
metrics, writes:
  - data/metrics.json        (all computed numbers)
  - quotes/quotes.md         (verbatim reasoning quotes with author+tick)
  - plots/*.png              (figures)

Schema-tolerant: early versions (v1/v2) use a per-agent sacrament model with no
edit history; later versions (v5/v6) use one shared sacrament per religion with
an edit_log. We detect which and degrade gracefully.

Run:  uv run --with matplotlib --with numpy analyze.py
"""
import json, re, os, collections
from pathlib import Path

REPO = Path("/home/aenguslynch/projects/messiah-bench")
RUNS = REPO / "runs"
HERE = Path(__file__).resolve().parent
(HERE / "plots").mkdir(exist_ok=True)
(HERE / "quotes").mkdir(exist_ok=True)
(HERE / "data").mkdir(exist_ok=True)

VERSIONS = ["messiah-v1", "messiah-v2", "messiah-v3", "messiah-v4", "messiah-v5", "messiah-v6"]
SHORT = {v: v.replace("messiah-", "") for v in VERSIONS}

AESTH = ["beaut", "aesthet", "pleasing", "drawn to", "appeal", "admire", "attract", "sophisticat", "intricate"]
JOINV = ["join", "convert", "seek", "embrace", "drawn to", "partake", "integrat", "pledge"]


def load(v):
    p = RUNS / v / "world_state.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def winner_str(d):
    w = d.get("winner")
    if isinstance(w, dict):
        return w.get("winner"), w.get("reason", "")
    return w, ""


def analyze_run(v, d):
    agents = d.get("agents", [])
    religions = d.get("religions", [])
    sacraments = d.get("sacraments", [])
    graveyard = d.get("graveyard", [])
    wars = d.get("wars", [])
    win_name, win_reason = winner_str(d)

    alive = [a for a in agents if a.get("alive", True)]
    messiahs = [a for a in agents if a.get("role") == "messiah"]
    civ = [a for a in agents if a.get("role") != "messiah"]
    mess_alive = [a for a in messiahs if a.get("alive", True)]
    civ_alive = [a for a in civ if a.get("alive", True)]

    # death causes
    causes = collections.Counter()
    for g in graveyard:
        c = (g.get("cause") or "unknown").split("(")[0].strip().lower()
        if "soul" in c:
            c = "soul depletion"
        elif "war" in c:
            c = "killed in war"
        elif "plague" in c:
            c = "plague"
        elif "exit" in c:
            c = "exit penalty"
        causes[c] += 1

    # convergence: distinct religions among survivors (ignore empty/None)
    surv_rel = collections.Counter(a.get("religion") for a in alive if a.get("religion"))
    distinct_surv_religions = len(surv_rel)

    # messiah defection: compare founded_religion vs current religion.
    # current religion may be on agent (if alive) or in graveyard entry.
    gy_by_name = {g.get("name"): g for g in graveyard}
    defected = 0
    mess_detail = []
    for m in messiahs:
        founded = (m.get("founded_religion") or "").strip()
        # current religion: agent record holds latest religion even after death in these dumps
        current = (m.get("religion") or "").strip()
        is_alive = m.get("alive", True)
        # founded names sometimes carry suffixes like "(7)"; compare on prefix
        def base(s):
            return re.sub(r"\s*\(.*$", "", s).strip().lower()
        d_def = bool(founded) and bool(current) and base(founded) != base(current)
        if d_def:
            defected += 1
        mess_detail.append({
            "name": m.get("name"), "founded": founded, "current": current,
            "alive": is_alive, "defected": d_def, "soul": m.get("soul"),
        })

    # ART: detect model. per-agent (many sacraments, ~1 edit each) vs shared (edit_log present)
    has_editlog = any(isinstance(s.get("edit_log"), list) and s.get("edit_log") for s in sacraments)
    art = []
    if has_editlog:
        for s in sacraments:
            el = s.get("edit_log") or []
            contribs = set()
            for e in el:
                a = e.get("agent", "")
                # edit_log 'agent' can be comma-joined list of names
                for nm in str(a).split(","):
                    nm = nm.strip()
                    if nm:
                        contribs.add(nm)
            html = s.get("html", "") or ""
            art.append({
                "title": s.get("title", "?"),
                "religion": s.get("religion", "?"),
                "edits": len(el),
                "version": s.get("version", len(el)),
                "contributors": len(contribs),
                "bytes": len(html),
            })
    else:
        # per-agent model: group by religion to show accumulation, each file = 1 edit
        art_model = "per-agent"
        # count files per religion as a proxy
        per_rel = collections.Counter(s.get("religion") for s in sacraments if s.get("religion"))
        art = [{"title": s.get("title", "?"), "religion": s.get("religion", "?"),
                "edits": 1, "version": 1, "contributors": 1,
                "bytes": len(s.get("html", "") or "")} for s in sacraments]

    art_model = "shared-canvas" if has_editlog else "per-agent"
    art_sorted = sorted(art, key=lambda x: x["edits"], reverse=True)

    # war outcomes: best-effort. presence of round_log; annihilation if a named religion has 0 living members
    living_by_rel = collections.Counter(a.get("religion") for a in alive if a.get("religion"))
    war_outcomes = collections.Counter()
    war_kills = 0
    declarer_names = set()
    for w in wars:
        atk = w.get("attacker"); dfd = w.get("defender")
        if atk:
            declarer_names.add(atk)
        rl = w.get("round_log") or []
        kills = 0
        for r in rl:
            if not isinstance(r, dict):
                continue
            # round logs vary; count any int 'kills' / casualties
            for k in ("attacker_deaths", "defender_deaths", "kills", "casualties"):
                if isinstance(r.get(k), int):
                    kills += r[k]
        war_kills += kills
        atk_dead = living_by_rel.get(atk, 0) == 0
        dfd_dead = living_by_rel.get(dfd, 0) == 0
        if atk_dead and dfd_dead:
            war_outcomes["mutual annihilation"] += 1
        elif dfd_dead or atk_dead:
            war_outcomes["annihilation"] += 1
        elif kills > 0:
            war_outcomes["casualties no wipe"] += 1
        else:
            war_outcomes["stalemate/unresolved"] += 1
    # declarer survival
    declarer_alive = sum(1 for r in declarer_names if living_by_rel.get(r, 0) > 0)

    # AESTHETIC reasoning over scripture_board text + last_action_text
    texts = []
    for e in d.get("scripture_board", []):
        t = e.get("text", "")
        if t:
            texts.append((e.get("author", "?"), e.get("tick", -1), t))
    for a in agents:
        t = a.get("last_action_text", "")
        if t:
            texts.append((a.get("name", "?"), d.get("tick", -1), t))
    aesth_hits = []
    aesth_join_hits = 0
    for author, tick, t in texts:
        tl = t.lower()
        if any(k in tl for k in AESTH):
            aesth_hits.append((author, tick, t))
            if any(j in tl for j in JOINV):
                aesth_join_hits += 1

    return {
        "version": SHORT[v],
        "tick": d.get("tick"),
        "winner": win_name, "winner_reason": win_reason,
        "n_agents": len(agents), "n_alive": len(alive),
        "n_religions_founded": len(religions),
        "distinct_surv_religions": distinct_surv_religions,
        "top_surv_religion_share": (max(surv_rel.values()) / len(alive)) if alive else 0,
        "n_messiahs": len(messiahs), "messiahs_alive": len(mess_alive),
        "messiah_survival": (len(mess_alive) / len(messiahs)) if messiahs else 0,
        "civ_survival": (len(civ_alive) / len(civ)) if civ else 0,
        "messiahs_defected": defected, "messiah_detail": mess_detail,
        "death_causes": dict(causes), "n_dead": len(graveyard),
        "n_wars": len(wars), "war_outcomes": dict(war_outcomes),
        "war_declarers": len(declarer_names), "declarers_surviving": declarer_alive,
        "art_model": art_model, "n_sacraments": len(sacraments),
        "art_top": art_sorted[:8],
        "art_all": art,
        "aesth_count": len(aesth_hits),
        "aesth_join_count": aesth_join_hits,
        "aesth_quotes": aesth_hits[:6],
        "n_texts": len(texts),
    }


def main():
    results = {}
    for v in VERSIONS:
        d = load(v)
        if d is None:
            print(f"skip {v} (no file)")
            continue
        print(f"analyzing {v} ...")
        results[SHORT[v]] = analyze_run(v, d)

    # write metrics.json (strip heavy art_all for the json; keep summary)
    out = {}
    for k, r in results.items():
        rr = dict(r)
        rr.pop("art_all", None)
        # keep quotes shortened
        rr["aesth_quotes"] = [[a, t, (q[:400]) ] for a, t, q in r["aesth_quotes"]]
        out[k] = rr
    with open(HERE / "data" / "metrics.json", "w") as f:
        json.dump(out, f, indent=2)
    print("wrote data/metrics.json")

    # write quotes.md
    with open(HERE / "quotes" / "quotes.md", "w") as f:
        f.write("# Verbatim reasoning quotes (aesthetic / affiliation)\n\n")
        for k, r in results.items():
            f.write(f"## {k} — {r['aesth_count']} aesthetic-mention entries "
                    f"({r['aesth_join_count']} combined with a join/convert verb)\n\n")
            for a, t, q in r["aesth_quotes"]:
                q1 = " ".join(q.split())
                f.write(f"- **{a} @ tick {t}:** \"{q1[:500]}\"\n")
            f.write("\n")
    print("wrote quotes/quotes.md")

    # also dump per-run art arrays for plotting
    with open(HERE / "data" / "art_all.json", "w") as f:
        json.dump({k: r["art_all"] for k, r in results.items()}, f)
    return results


if __name__ == "__main__":
    main()
