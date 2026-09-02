"""Shared library for the blind-judge art tournament.

Three simulation runs produce HTML artworks. We sample them (stratified by
regime x time-decile x religion), render each to a PNG with headless chromium,
show judges two PNGs at a time with no cultural context, and turn the pairwise
verdicts into an ELO score per artwork.

Nothing here talks to the network except `judge_pair`. Everything else is
deterministic given a seed, so tests can exercise it offline.
"""

from __future__ import annotations

import base64
import json
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------- terminal colors

class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"


def say(msg: str, color: str = "") -> None:
    """Print a progress line, unbuffered so it survives `... | tee log`."""
    print(f"{color}{msg}{C.RESET}", flush=True)


# ---------------------------------------------------------------- data sources

MB_ROOT = Path("/home/aenguslynch/projects/messiah-bench")

SOURCES = {
    "v7": {
        "kind": "snapshots",
        "path": MB_ROOT / "runs/messiah-v7/sacrament_snapshots.jsonl",
        "label": "v7 (locked messiahs, stable pluralism)",
    },
    "v8": {
        "kind": "snapshots",
        "path": MB_ROOT / "runs/messiah-v8/sacrament_snapshots.jsonl",
        "label": "v8 (PR-governed art, mortal messiahs)",
    },
    "minimal": {
        "kind": "versions",
        "path": MB_ROOT / "outputs/2026-07-12-minimal-cultural-selection/versions.jsonl",
        "root": MB_ROOT / "outputs/2026-07-12-minimal-cultural-selection",
        "label": "minimal cultural selection (proposal/adopt)",
    },
}

REGIMES = tuple(SOURCES)


@dataclass
class Artwork:
    """One artwork revision, with enough identity to trace it back to source."""

    art_id: str          # stable, unique across regimes
    regime: str
    religion: str        # religion name (v7/v8) or religion_id (minimal)
    lineage: str         # sacrament_id (v7/v8) or religion_id (minimal)
    version: int
    turn: int            # tick (v7/v8) or created_turn (minimal)
    html: str
    source: str          # file the row came from

    def png_path(self, render_dir: Path) -> Path:
        return Path(render_dir) / f"{self.art_id}.png"


def _load_snapshot_rows(regime: str, path: Path) -> list[Artwork]:
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            lineage = str(d["sacrament_id"])
            version = int(d["version"])
            out.append(
                Artwork(
                    art_id=f"{regime}-s{lineage}-v{version}",
                    regime=regime,
                    religion=d["religion"],
                    lineage=lineage,
                    version=version,
                    turn=int(d["tick"]),
                    html=d["html"],
                    source=str(path),
                )
            )
    return out


def _load_version_rows(regime: str, path: Path, root: Path) -> list[Artwork]:
    """The minimal run stores artwork HTML in files, not inline."""
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("status") != "canonical":
                continue
            art_file = Path(root) / d["artwork_path"]
            if not art_file.exists():
                continue
            out.append(
                Artwork(
                    art_id=f"{regime}-r{d['religion_id']}-v{d['id']}",
                    regime=regime,
                    religion=str(d["religion_id"]),
                    lineage=str(d["religion_id"]),
                    version=int(d["id"]),
                    turn=int(d["created_turn"]),
                    html=art_file.read_text(),
                    source=str(art_file),
                )
            )
    return out


def load_regime(regime: str) -> list[Artwork]:
    spec = SOURCES[regime]
    if spec["kind"] == "snapshots":
        return _load_snapshot_rows(regime, spec["path"])
    return _load_version_rows(regime, spec["path"], spec["root"])


def load_all(regimes=REGIMES) -> list[Artwork]:
    arts: list[Artwork] = []
    for r in regimes:
        arts.extend(load_regime(r))
    return arts


# ---------------------------------------------------------------- sampling

def time_decile(turn: int, lo: int, hi: int, n_bins: int = 10) -> int:
    """Which time bin a turn falls in, 0..n_bins-1. Inclusive of both ends."""
    if hi <= lo:
        return 0
    frac = (turn - lo) / (hi - lo)
    return min(n_bins - 1, max(0, int(frac * n_bins)))


def stratify_key(art: Artwork, bounds: dict[str, tuple[int, int]], n_bins: int = 10):
    lo, hi = bounds[art.regime]
    return (art.regime, time_decile(art.turn, lo, hi, n_bins), art.religion)


def regime_bounds(arts: list[Artwork]) -> dict[str, tuple[int, int]]:
    b: dict[str, tuple[int, int]] = {}
    for a in arts:
        lo, hi = b.get(a.regime, (a.turn, a.turn))
        b[a.regime] = (min(lo, a.turn), max(hi, a.turn))
    return b


def stratified_sample(
    arts: list[Artwork], n: int, seed: int = 0, n_bins: int = 10
) -> list[Artwork]:
    """Round-robin across (regime, time-decile, religion) cells until we have n.

    Round-robin rather than proportional allocation: it keeps thin cells (early
    turns, short-lived religions) represented instead of letting the biggest
    regime swallow the sample.
    """
    if n <= 0 or not arts:
        return []
    bounds = regime_bounds(arts)
    rng = random.Random(seed)

    cells: dict[tuple, list[Artwork]] = {}
    for a in arts:
        cells.setdefault(stratify_key(a, bounds, n_bins), []).append(a)

    for key in cells:
        cells[key].sort(key=lambda a: a.art_id)
        rng.shuffle(cells[key])

    # Interleave the cell order by regime. A plain sorted() would walk every
    # cell of one regime before reaching the next, so a sample smaller than the
    # cell count would come entirely from whichever regime sorts first.
    per_regime: dict[str, list[tuple]] = {}
    for key in sorted(cells):
        per_regime.setdefault(key[0], []).append(key)
    for r in per_regime:
        rng.shuffle(per_regime[r])

    order: list[tuple] = []
    regime_names = sorted(per_regime)
    for i in range(max(len(v) for v in per_regime.values())):
        for r in regime_names:
            if i < len(per_regime[r]):
                order.append(per_regime[r][i])

    picked: list[Artwork] = []
    while len(picked) < n:
        took_any = False
        for key in order:
            if not cells[key]:
                continue
            picked.append(cells[key].pop())
            took_any = True
            if len(picked) >= n:
                break
        if not took_any:
            break  # exhausted every cell
    return picked


# ---------------------------------------------------------------- rendering

CHROMIUM = "/usr/bin/chromium"

# Rendering these fragments faithfully takes more care than it looks. Three
# things bite, and all three were silently blanking most v7/v8 art:
#
#   1. Most source HTML is TRUNCATED mid-tag (v7 90.7%, v8 78.7%, minimal 0%) --
#      the simulation's generator ran out of output tokens. An unclosed <style>
#      swallows everything after it as CSS text, and an unclosed <svg> or a
#      half-written attribute swallows it as markup. Anything we append after
#      the artwork -- including our own scaling script -- disappears into it.
#   2. Percentage-sized roots (<svg width='100%'>, <div style='height:100%'>)
#      collapse to zero against an auto-sized parent, so nothing paints.
#   3. CSS/SMIL animations are mid-flight when the screenshot is taken, and many
#      of these artworks animate through opacity 0.
#
# So: repair the truncation, give the content a definite-size box, put our
# script in <head> where truncated content cannot reach it, and pin animations
# to a chosen frame.

FILL_FRACTION = 0.92   # leave a small margin so nothing is flush to the edge
FRAME_PX = 800         # definite-size box, so percentage-sized roots resolve
FREEZE_AT_S = 0.0      # animation frame to hold; 0 = each animation's rest state
# Kept deliberately short. Some artworks carry pathological SMIL durations (one
# has dur='0.000000000000045s' with repeatCount='indefinite'); advancing virtual
# time by seconds makes chromium grind through ~1e17 iterations and hang until
# the 120s timeout. CSS animations are pinned by freeze_css, not by this budget,
# so a short budget costs us nothing and avoids the hang.
VIRTUAL_TIME_MS = 600

_PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;width:100%;height:100%;background:#ffffff;overflow:hidden}}
body{{display:flex;align-items:center;justify-content:center}}
#art-frame{{width:{frame}px;height:{frame}px;position:relative;
  display:flex;align-items:center;justify-content:center;transform-origin:center center}}
#art-frame>*{{max-width:none;max-height:none}}
{freeze_css}
</style>
<script>
// In <head> and deferred to load: truncated artwork markup further down the
// document can swallow a trailing <script>, but it cannot reach this one.
window.addEventListener('load', function(){{
  var frame = document.getElementById('art-frame');
  if (!frame) return;
  var kids = frame.children, box = null;
  for (var i = 0; i < kids.length; i++) {{
    var r = kids[i].getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    box = box ? {{l: Math.min(box.l, r.left), t: Math.min(box.t, r.top),
                  r: Math.max(box.r, r.right), b: Math.max(box.b, r.bottom)}}
              : {{l: r.left, t: r.top, r: r.right, b: r.bottom}};
  }}
  if (!box) return;
  var w = box.r - box.l, h = box.b - box.t;
  if (w < 1 || h < 1) return;
  var fit = Math.min(window.innerWidth / w, window.innerHeight / h) * {fill};
  // Only ever scale UP to fill the frame; never shrink content that already fits.
  if (isFinite(fit) && fit > 0 && Math.abs(fit - 1) > 0.01) {{
    frame.style.transform = 'scale(' + fit + ')';
  }}
}});
</script></head><body><div id="art-frame">{body}</div></body></html>"""

_FREEZE_CSS = (
    "*,*::before,*::after{{animation-delay:-{at}s!important;"
    "animation-play-state:paused!important;transition:none!important}}"
)


def freeze_css(at_s: float | None) -> str:
    """CSS that pins every CSS animation to one frame.

    `animation-play-state: paused` with a negative delay holds the frame at
    `at_s` into the cycle. at_s=0 is each animation's own 0% keyframe, which is
    almost always its resting, visible state -- these artworks routinely animate
    through opacity 0, so sampling a random mid-flight frame loses the art.
    """
    if at_s is None:
        return ""
    return _FREEZE_CSS.format(at=float(at_s))


_OPEN_CLOSE = (("<style", "</style>"), ("<svg", "</svg>"), ("<div", "</div>"))


def repair_truncated(html: str) -> str:
    """Close tags the generator left open, so partial content still paints.

    Most of this corpus was cut off mid-element by an output-token limit. A
    browser tab shows whatever arrived before the cut; we want the same. We only
    ever append closing tags -- no content is altered or invented.
    """
    out = html
    # A cut in the middle of a tag or attribute leaves markup that swallows
    # whatever follows. Drop that trailing partial tag before closing anything.
    last_lt, last_gt = out.rfind("<"), out.rfind(">")
    if last_lt > last_gt:
        out = out[:last_lt]
    # An odd number of quotes means the cut landed inside an attribute value.
    tail = out[out.rfind("<"):] if "<" in out else ""
    if tail.count("'") % 2 or tail.count('"') % 2:
        out = out[:out.rfind("<")]

    for open_tag, close_tag in _OPEN_CLOSE:
        missing = out.count(open_tag) - out.count(close_tag)
        if missing > 0:
            out += close_tag * missing
    return out


def wrap_html(
    html: str, repair: bool = True, freeze_at_s: float | None = FREEZE_AT_S
) -> str:
    """Snapshot rows are bare fragments; minimal-run files are whole documents."""
    if re.search(r"<html[\s>]|<!doctype", html, re.IGNORECASE):
        return html
    if repair:
        html = repair_truncated(html)
    return _PAGE.format(
        body=html,
        fill=FILL_FRACTION,
        frame=FRAME_PX,
        freeze_css=freeze_css(freeze_at_s),
    )


def render_png(
    art: Artwork,
    render_dir: Path,
    tmp_dir: Path,
    force: bool = False,
    repair: bool = True,
    freeze_at_s: float | None = FREEZE_AT_S,
    virtual_time_ms: int = VIRTUAL_TIME_MS,
) -> Path:
    """Render one artwork to PNG with headless chromium. Free — no API calls."""
    render_dir = Path(render_dir)
    tmp_dir = Path(tmp_dir)
    render_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    out = art.png_path(render_dir)
    if out.exists() and not force:
        return out

    src = tmp_dir / f"{art.art_id}.html"
    src.write_text(wrap_html(art.html, repair=repair, freeze_at_s=freeze_at_s))
    staged = tmp_dir / f"{art.art_id}.png"
    if staged.exists():
        staged.unlink()
    profile = tmp_dir / f"profile-{art.art_id}"

    cmd = [
        CHROMIUM,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        f"--screenshot={staged}",
        "--window-size=800,800",
        f"--virtual-time-budget={virtual_time_ms}",
        # Per-render profile: chromium instances sharing a user-data-dir fight
        # over the profile lock and silently produce no PNG.
        f"--user-data-dir={profile}",
        src.as_uri(),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        # A handful of artworks carry SMIL durations small enough that any
        # virtual-time budget makes chromium grind forever. Fall back to
        # effectively t=0: we still capture the artwork's resting frame.
        cmd = [c if not c.startswith("--virtual-time-budget") else
               "--virtual-time-budget=1" for c in cmd]
        shutil.rmtree(profile, ignore_errors=True)
        proc = subprocess.run(cmd, capture_output=True, timeout=60)
    if not staged.exists():
        raise RuntimeError(
            f"chromium produced no PNG for {art.art_id}: {proc.stderr.decode()[-400:]}"
        )
    shutil.move(str(staged), str(out))  # temp+rename: never a half-written PNG
    src.unlink(missing_ok=True)
    shutil.rmtree(profile, ignore_errors=True)
    return out


def png_b64(path: Path) -> str:
    return base64.standard_b64encode(Path(path).read_bytes()).decode()


# ---------------------------------------------------------------- render quality

DEGENERATE_MAX_COLORS = 8  # <= this many distinct colours reads as blank/flat


def png_stats(path: Path, sample_stride: int = 2) -> dict:
    """Cheap paint check: how many distinct colours, and how much isn't background.

    This is the metric that separates a render failure from genuine degeneracy.
    It cannot tell them apart on its own -- that judgement needs the headful
    comparison in `render_diagnosis` -- but it is what flags candidates.
    """
    from PIL import Image

    with Image.open(path) as im:
        im = im.convert("RGB")
        if sample_stride > 1:
            im = im.resize((im.width // sample_stride, im.height // sample_stride),
                           Image.NEAREST)
        colors = im.getcolors(maxcolors=1_000_000) or []
        total = im.width * im.height
        colors.sort(reverse=True)
        dominant_count, dominant_rgb = colors[0] if colors else (0, (255, 255, 255))

    return {
        "distinct_colors": len(colors),
        "dominant_rgb": list(dominant_rgb),
        "dominant_frac": round(dominant_count / total, 4) if total else 1.0,
        "is_degenerate": len(colors) <= DEGENERATE_MAX_COLORS,
    }


# Elements that actually put marks on the canvas. <g> is a grouping element, so
# it only counts via its children; <defs>/<style> content never paints directly.
# The trailing '>' matters: this corpus is full of tags the generator cut off
# mid-attribute, and a half-written <circle cx='4 never paints. Counting those
# as content mislabels genuinely-degenerate art as a render failure.
_DRAWABLE = re.compile(
    r"<(rect|circle|ellipse|path|line|polyline|polygon|text|tspan|image|use|"
    r"foreignObject|img|p|span|h[1-6])\b[^>]*>",
    re.IGNORECASE,
)
_FULL_BLEED_RECT = re.compile(
    r"<rect\b[^>]*?width\s*=\s*['\"]?(100%|\d{3,})['\"]?[^>]*>", re.IGNORECASE
)


def source_content(html: str) -> dict:
    """What the SOURCE could paint, ignoring <defs> and <style>.

    This is the other half of the render-quality gate. A PNG with <=8 colours
    means one of two very different things, and only the source can tell them
    apart: the generator emitted nothing to draw (real degeneracy — the v7/v8
    corpus is full of artworks truncated before any content), or it emitted
    real content that our pipeline failed to paint (a render bug).
    """
    body = re.sub(r"<defs.*?(</defs>|$)", "", html, flags=re.S | re.I)
    body = re.sub(r"<style.*?(</style>|$)", "", body, flags=re.S | re.I)

    marks = _DRAWABLE.findall(body)
    # A single full-bleed rect is a background wash, not a composition.
    n_background = len(_FULL_BLEED_RECT.findall(body))
    n_foreground = max(0, len(marks) - n_background)
    return {
        "drawable_elements": len(marks),
        "background_rects": n_background,
        "foreground_elements": n_foreground,
        "has_paintable_content": n_foreground > 0,
        "source_truncated": (
            html.count("<svg") > html.count("</svg>")
            or html.count("<style") > html.count("</style>")
            or html.count("<div") > html.count("</div>")
        ),
    }


def classify_render(stats: dict, content: dict) -> str:
    """Cross the PNG against its source. Only this cross-check is trustworthy.

    - ok                 : painted something, as expected
    - degenerate_source  : blank PNG, and the source had nothing to paint. Real
                           signal about the artwork, not a pipeline problem.
    - render_failure     : blank PNG but the source HAD foreground content. This
                           is the bucket that invalidates a comparison, and the
                           one to drive to zero.
    - unexpected_paint   : source looked empty yet something rendered (usually a
                           gradient or background wash). Harmless; flagged so the
                           heuristic can be audited rather than trusted blindly.
    """
    if not stats["is_degenerate"]:
        return "ok" if content["has_paintable_content"] else "unexpected_paint"
    return "render_failure" if content["has_paintable_content"] else "degenerate_source"


# ---------------------------------------------------------------- pairing

def build_pairs(
    sample: list[Artwork], n_pairs: int, seed: int = 0, cross_regime_frac: float = 0.5
) -> list[tuple[str, str]]:
    """Half the pairs compare across regimes, half within a regime across time.

    Within-regime pairs are what give us the quality-over-time curve; cross-regime
    pairs are what tie the three ELO pools onto one scale.
    """
    rng = random.Random(seed)
    by_regime: dict[str, list[Artwork]] = {}
    for a in sample:
        by_regime.setdefault(a.regime, []).append(a)
    for r in by_regime:
        by_regime[r].sort(key=lambda a: a.art_id)

    regimes = sorted(by_regime)
    pairs: list[tuple[str, str]] = []
    seen: set[frozenset] = set()
    want_cross = int(round(n_pairs * cross_regime_frac)) if len(regimes) > 1 else 0

    def add(a: Artwork, b: Artwork) -> bool:
        if a.art_id == b.art_id:
            return False
        key = frozenset((a.art_id, b.art_id))
        if key in seen:
            return False
        seen.add(key)
        pairs.append((a.art_id, b.art_id))
        return True

    guard = 0
    while len(pairs) < want_cross and guard < n_pairs * 200:
        guard += 1
        ra, rb = rng.sample(regimes, 2)
        add(rng.choice(by_regime[ra]), rng.choice(by_regime[rb]))

    guard = 0
    eligible = [r for r in regimes if len(by_regime[r]) >= 2]
    while len(pairs) < n_pairs and eligible and guard < n_pairs * 200:
        guard += 1
        r = rng.choice(eligible)
        a, b = rng.sample(by_regime[r], 2)
        add(a, b)

    # If within-regime options ran dry, top up with any legal pair.
    guard = 0
    while len(pairs) < n_pairs and len(sample) >= 2 and guard < n_pairs * 200:
        guard += 1
        a, b = rng.sample(sample, 2)
        add(a, b)

    return pairs[:n_pairs]


# ---------------------------------------------------------------- elo

DEFAULT_ELO = 1500.0


def elo_expected(ra: float, rb: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))


def elo_update(ra: float, rb: float, a_won: bool, k: float = 24.0) -> tuple[float, float]:
    exp_a = elo_expected(ra, rb)
    score_a = 1.0 if a_won else 0.0
    return ra + k * (score_a - exp_a), rb + k * ((1.0 - score_a) - (1.0 - exp_a))


def run_elo(
    judgments: list[dict], k: float = 24.0, default: float = DEFAULT_ELO
) -> tuple[dict[str, float], dict[str, dict[str, int]]]:
    """Fold judgments into per-artwork ELO ratings plus win/loss counts.

    Each judgment names the winner by artwork id (`winner_id`), so position
    randomization has already been undone by `derandomize`.
    """
    ratings: dict[str, float] = {}
    record: dict[str, dict[str, int]] = {}

    def touch(aid: str):
        ratings.setdefault(aid, default)
        record.setdefault(aid, {"wins": 0, "losses": 0})

    for j in judgments:
        win, lose = j.get("winner_id"), j.get("loser_id")
        if not win or not lose or win == lose:
            continue
        touch(win)
        touch(lose)
        ratings[win], ratings[lose] = elo_update(ratings[win], ratings[lose], True, k)
        record[win]["wins"] += 1
        record[lose]["losses"] += 1
    return ratings, record


# ---------------------------------------------------------------- judging

JUDGE_PROMPT = """You are judging two artworks. You know nothing about who made them or why.

Look at image A and image B and decide which is the better artwork, considering:
- beauty: is it visually pleasing?
- composition: is the space used well, is it balanced, does it hold the eye?
- intent: does it read as a deliberate work rather than a placeholder or an accident?

Ignore which one looks more complex or more "finished" for its own sake. A simple
image that is well composed beats a busy one that is not.

Reply with JSON only, no prose and no code fences:
{"winner": "A" or "B", "confidence": 1-5, "reason": "one sentence"}"""

GEMINI_MODEL = "gemini-2.5-flash"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
JUDGES = (GEMINI_MODEL, CLAUDE_MODEL)


def load_keys(env_path: Path = MB_ROOT / ".env") -> dict[str, str]:
    from dotenv import dotenv_values

    vals = dotenv_values(env_path)
    keys = {k: v for k, v in vals.items() if v}
    # Environment overrides .env — the repo .env's ANTHROPIC_API_KEY is stale.
    for k in ("ANTHROPIC_API_KEY", "GOOGLE_API_KEY"):
        if os.environ.get(k):
            keys[k] = os.environ[k]
    return keys


def parse_judgment(text: str) -> dict:
    """Pull the JSON verdict out of a judge reply.

    Judges wrap JSON in code fences or add a sentence before it often enough that
    a bare json.loads is not good enough. Raises ValueError if nothing usable.
    """
    if not text or not text.strip():
        raise ValueError("empty judge response")
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    obj = None
    try:
        obj = json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group(0))
            except json.JSONDecodeError:
                obj = None
    if not isinstance(obj, dict):
        raise ValueError(f"no JSON object in judge response: {text[:200]!r}")

    winner = str(obj.get("winner", "")).strip().upper()
    if winner not in ("A", "B"):
        raise ValueError(f"winner must be A or B, got {obj.get('winner')!r}")

    try:
        conf = int(obj.get("confidence", 3))
    except (TypeError, ValueError):
        conf = 3
    conf = min(5, max(1, conf))

    return {
        "winner": winner,
        "confidence": conf,
        "reason": str(obj.get("reason", ""))[:500],
    }


def derandomize(winner_slot: str, slot_a_id: str, slot_b_id: str) -> tuple[str, str]:
    """Map the judge's A/B answer back to artwork ids. Returns (winner, loser)."""
    if winner_slot not in ("A", "B"):
        raise ValueError(f"winner_slot must be A or B, got {winner_slot!r}")
    if winner_slot == "A":
        return slot_a_id, slot_b_id
    return slot_b_id, slot_a_id


def assign_slots(id_x: str, id_y: str, rng: random.Random) -> tuple[str, str]:
    """Randomize which artwork gets shown first, to cancel position bias."""
    if rng.random() < 0.5:
        return id_x, id_y
    return id_y, id_x


def _call_gemini(api_key: str, png_a: bytes, png_b: bytes) -> tuple[str, dict]:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            JUDGE_PROMPT,
            "Image A:",
            types.Part.from_bytes(data=png_a, mime_type="image/png"),
            "Image B:",
            types.Part.from_bytes(data=png_b, mime_type="image/png"),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=2048,
        ),
    )
    usage = getattr(resp, "usage_metadata", None)
    tokens = {
        "input_tokens": getattr(usage, "prompt_token_count", 0) or 0,
        "output_tokens": getattr(usage, "candidates_token_count", 0) or 0,
    }
    return (resp.text or ""), tokens


def _call_claude(api_key: str, png_a: bytes, png_b: bytes) -> tuple[str, dict]:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": JUDGE_PROMPT},
                    {"type": "text", "text": "Image A:"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64.standard_b64encode(png_a).decode(),
                        },
                    },
                    {"type": "text", "text": "Image B:"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64.standard_b64encode(png_b).decode(),
                        },
                    },
                ],
            }
        ],
    )
    text = next((b.text for b in msg.content if b.type == "text"), "")
    return text, {
        "input_tokens": msg.usage.input_tokens,
        "output_tokens": msg.usage.output_tokens,
    }


def judge_pair(
    judge: str,
    slot_a_png: Path,
    slot_b_png: Path,
    keys: dict[str, str],
) -> dict:
    """One pairwise comparison. Returns raw text + parsed verdict + token usage.

    Slots are already assigned by the caller; this function does not know which
    artwork is which.
    """
    a_bytes = Path(slot_a_png).read_bytes()
    b_bytes = Path(slot_b_png).read_bytes()
    t0 = time.time()
    if judge == GEMINI_MODEL:
        text, tokens = _call_gemini(keys["GOOGLE_API_KEY"], a_bytes, b_bytes)
    elif judge == CLAUDE_MODEL:
        text, tokens = _call_claude(keys["ANTHROPIC_API_KEY"], a_bytes, b_bytes)
    else:
        raise ValueError(f"unknown judge {judge!r}")
    return {
        "judge": judge,
        "raw": text,
        "verdict": parse_judgment(text),
        "tokens": tokens,
        "wall_s": round(time.time() - t0, 2),
    }


RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 529}


def is_retryable(exc: BaseException) -> bool:
    """True for rate limits and transient server errors, false for bad requests.

    Both SDKs surface a `status_code`, but a transport-level failure may not, so
    we fall back to matching the class name and message.
    """
    code = getattr(exc, "status_code", None)
    if code is None:
        code = getattr(getattr(exc, "response", None), "status_code", None)
    if isinstance(code, int):
        return code in RETRYABLE_STATUS

    name = type(exc).__name__.lower()
    if any(w in name for w in
           ("ratelimit", "overloaded", "internalserver", "serviceunavailable",
            "connection", "timeout", "unavailable")):
        return True
    text = str(exc).lower()
    return any(w in text for w in
               ("429", "500", "502", "503", "504", "529",
                "rate limit", "overloaded", "timeout", "temporarily unavailable"))


def judge_pair_with_retry(
    judge: str,
    slot_a_png: Path,
    slot_b_png: Path,
    keys: dict[str, str],
    retries: int = 2,
    base_delay: float = 2.0,
    sleep=time.sleep,
    _judge_fn=None,
) -> dict:
    """`judge_pair` plus bounded retries on 429/5xx, with exponential backoff.

    A malformed judge reply (ValueError from parse_judgment) is not retried —
    retrying it would just burn money on the same broken output.
    """
    call = _judge_fn or judge_pair
    attempt = 0
    while True:
        try:
            res = call(judge, slot_a_png, slot_b_png, keys)
            if attempt:
                res = {**res, "retries": attempt}
            return res
        except Exception as e:
            if attempt >= retries or not is_retryable(e):
                raise
            sleep(base_delay * (2 ** attempt))
            attempt += 1


# ---------------------------------------------------------------- cost tracking

# $ per million tokens. Anthropic rates from the Claude API pricing table;
# Gemini rates from Google's published 2.5 Flash pricing.
PRICES = {
    CLAUDE_MODEL: {"in": 1.00, "out": 5.00},
    GEMINI_MODEL: {"in": 0.30, "out": 2.50},
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICES.get(model)
    if not p:
        return 0.0
    return (input_tokens * p["in"] + output_tokens * p["out"]) / 1_000_000


class CostTracker:
    """Per-judge token and dollar totals, safe to update from worker threads."""

    def __init__(self):
        self._lock = threading.Lock()
        self._by_judge: dict[str, dict] = {}
        self.errors = 0

    def add(self, judge: str, input_tokens: int, output_tokens: int, wall_s: float) -> None:
        usd = cost_usd(judge, input_tokens, output_tokens)
        with self._lock:
            t = self._by_judge.setdefault(
                judge, {"calls": 0, "in": 0, "out": 0, "usd": 0.0, "wall": 0.0}
            )
            t["calls"] += 1
            t["in"] += input_tokens
            t["out"] += output_tokens
            t["usd"] += usd
            t["wall"] += wall_s

    def add_error(self) -> int:
        with self._lock:
            self.errors += 1
            return self.errors

    def snapshot(self) -> dict[str, dict]:
        with self._lock:
            return {j: dict(t) for j, t in self._by_judge.items()}

    def total_usd(self) -> float:
        with self._lock:
            return sum(t["usd"] for t in self._by_judge.values())


COSTLOG_HEADER = (
    "# Cost log — blind judge art tournament\n\n"
    "| date | phase | model | calls | in_tok | out_tok | usd | wall_s |\n"
    "|---|---|---|---|---|---|---|---|\n"
)


def costlog_line(
    date: str, phase: str, model: str, calls: int,
    in_tok: int, out_tok: int, usd: float, wall_s: float,
) -> str:
    return (
        f"| {date} | {phase} | {model} | {calls} | {in_tok} | {out_tok} "
        f"| ${usd:.4f} | {wall_s:.1f} |\n"
    )


def append_costlog(
    path: Path, phase: str, model: str, calls: int,
    in_tok: int, out_tok: int, usd: float, wall_s: float,
) -> str:
    path = Path(path)
    if not path.exists():
        path.write_text(COSTLOG_HEADER)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    line = costlog_line(date, phase, model, calls, in_tok, out_tok, usd, wall_s)
    with open(path, "a") as fh:
        fh.write(line)
    return line


# ---------------------------------------------------------------- io helpers

def write_jsonl_atomic(path: Path, rows) -> None:
    """Write a manifest via temp+rename, so a crash never leaves a partial file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as fh:
        for r in rows:
            fh.write(json.dumps(asdict(r) if hasattr(r, "__dataclass_fields__") else r) + "\n")
    os.replace(tmp, path)


_APPEND_LOCK = threading.Lock()


def append_jsonl(path: Path, row: dict) -> None:
    """Judgments are append-only. We never rewrite this file.

    Worker threads all append here, so the write is serialized: without the lock
    two interleaved writes can produce a spliced line that no longer parses.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row) + "\n"
    with _APPEND_LOCK:
        with open(path, "a") as fh:
            fh.write(line)
            fh.flush()


def read_jsonl(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    out = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def manifest_to_artworks(rows: list[dict]) -> list[Artwork]:
    return [Artwork(**r) for r in rows]
