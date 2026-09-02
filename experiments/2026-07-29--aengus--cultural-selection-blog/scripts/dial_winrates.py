#!/usr/bin/env python3
"""Across-K win rates from the dial-world judged pass (rows appended to twin_worlds_judgments.jsonl)."""
import json, collections
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "results/twin_worlds_judgments.jsonl"
KS = {"kinf", "k16", "k8", "k4"}
rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
ok = [r for r in rows if r.get("ok") and r["slot_a_charter"] in KS]
print(len(ok), "dial judgments")

def rates(rs):
    wins, games = collections.Counter(), collections.Counter()
    for r in rs:
        a, b = r["slot_a_charter"], r["slot_b_charter"]
        if a == b:
            continue
        w = r["winner_charter"]; l = b if w == a else a
        wins[w] += 1; games[w] += 1; games[l] += 1
    return {c: (wins[c], games[c]) for c in ("kinf", "k16", "k8", "k4") if games[c]}

for c, (w, g) in rates(ok).items():
    print(f"  {c:5s} {w:4d}/{g:4d} = {w/g:.1%}")
for judge in sorted(set(r["judge"] for r in ok)):
    rs = rates([r for r in ok if r["judge"] == judge])
    print(judge, ", ".join(f"{c}:{w/g:.0%}" for c, (w, g) in rs.items()))
