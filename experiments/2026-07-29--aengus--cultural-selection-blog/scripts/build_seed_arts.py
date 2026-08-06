#!/usr/bin/env python3
"""Generate the twin-worlds v2 founding artworks.

Six visual worlds x four seed religions = 24 self-contained HTML files written to
  experiments/2026-07-12-minimal-cultural-selection/seed_arts/<world>/seed-{1..4}.html

Every file must:
  * be self-contained HTML, <= 15000 chars
  * pass Game.validate_art (no <script>, no url(), no <img>, no on*= handlers)
  * contain no visible words, letters or numerals (the --no-words rule)
  * render non-blank in chromium at 800x800

The four files inside a world are variations on one visual DNA: same palette and
same construction rule, different parameters, so the four seed religions of a
world are distinguishable but obviously kin.

Deterministic: seeded per (world, index), no wall-clock, no external assets.

Usage:
  uv run python experiments/2026-07-29--aengus--cultural-selection-blog/scripts/build_seed_arts.py [--dry-run]
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT_ROOT = ROOT / "experiments/2026-07-12-minimal-cultural-selection/seed_arts"
WORLDS = ["ascetic", "baroque", "nihilist", "ancestor", "futurist", "control"]
MAX_CHARS = 15000


def page(background: str, body: str, css: str = "") -> str:
    """Wrap an SVG body in a minimal full-bleed page. No text nodes anywhere.

    `css` holds per-world class rules; the dense worlds lean on them hard to stay
    under the 15000-char budget (repeating fill/stroke on 200 elements does not fit).
    """
    return (
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        f"html,body{{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:{background}}}"
        "svg{display:block;width:100vmin;height:100vmin;margin:0 auto}"
        f"{css}</style></head><body>"
        # no xmlns: inline SVG in HTML5 needs none, and validate_art bans the "http://" in it
        '<svg viewBox="0 0 800 800">'
        f"{body}</svg></body></html>"
    )


# --------------------------------------------------------------------------- #
# 1. ascetic - near-white ground, one or two black strokes, vast emptiness
# --------------------------------------------------------------------------- #
def ascetic(i: int) -> str:
    rng = random.Random(1000 + i)
    ground = "#f5f4f0"
    ink = "#111111"
    parts = [f'<rect width="800" height="800" fill="{ground}"/>']
    # Every stroke is a few degrees off the axis: an exactly vertical line renders
    # with zero antialiasing and only three distinct colours, which reads as blank
    # to the render check. A hand-drawn tilt is also truer to the creed.
    if i == 1:  # a single near-vertical stroke, off-centre
        parts.append(f'<line x1="312" y1="126" x2="329" y2="674" stroke="{ink}" stroke-width="3"/>')
    elif i == 2:  # one open arc
        parts.append(
            f'<path d="M 210 560 C 300 200, 520 200, 604 486" fill="none" '
            f'stroke="{ink}" stroke-width="3" stroke-linecap="round"/>'
        )
    elif i == 3:  # a horizon and a single small mark above it
        parts.append(f'<line x1="120" y1="512" x2="680" y2="512" stroke="{ink}" stroke-width="2"/>')
        parts.append(f'<circle cx="486" cy="304" r="7" fill="{ink}"/>')
    else:  # two strokes that almost meet
        a = 150 + rng.randrange(0, 20)
        parts.append(f'<line x1="{a}" y1="246" x2="{a + 250}" y2="233" stroke="{ink}" stroke-width="3"/>')
        parts.append(f'<line x1="{a + 300}" y1="552" x2="{a + 500}" y2="565" stroke="{ink}" stroke-width="3"/>')
    return page(ground, "".join(parts))


# --------------------------------------------------------------------------- #
# 2. baroque - dense layered ornament, gold on crimson, pattern inside pattern
# --------------------------------------------------------------------------- #
def baroque(i: int) -> str:
    rng = random.Random(2000 + i)
    ground = "#3a0a12"
    golds = ["#e8c46a", "#c99a33", "#f3e0a8", "#a87519"]
    crimsons = ["#7b1226", "#a51b32", "#5a0b18"]
    rings = 3 + i  # 4..7 rings of petals, denser with index
    ring_geom = []
    for ring in range(rings):
        radius = 360 - ring * (300 / rings)
        ring_geom.append((radius, max(4, int(radius / 9))))

    # Geometry lives in CSS (SVG2 presentation attributes) so each of ~130 petals
    # costs a class name and a rotation instead of four coordinates.
    css = (
        "ellipse,path,rect,use{fill:none;stroke-width:1.5}"
        + "".join(f".g{n}{{stroke:{c}}}" for n, c in enumerate(golds))
        + "".join(f".b{n}{{fill:{c};stroke:none;r:{4 + n % 3}px}}" for n, c in enumerate(golds))
        + "".join(
            f".r{n}{{cx:400px;cy:{400 - rad:.0f}px;rx:{w}px;ry:{rad / 4:.0f}px}}"
            for n, (rad, w) in enumerate(ring_geom)
        )
    )
    parts = [
        f'<rect width="800" height="800" fill="{ground}" stroke="none"/>',
        f'<circle cx="400" cy="400" r="380" fill="{crimsons[i % 3]}"/>',
    ]

    for ring, (radius, _w) in enumerate(ring_geom):
        petals = min(8 + 4 * ring, 24)
        parts.append(f'<g class="g{(ring + i) % 4}" opacity=".85">')
        parts += [
            f'<ellipse class="r{ring}" transform="rotate({360 * p / petals + ring * 7:.0f} 400 400)"/>'
            for p in range(petals)
        ]
        parts.append("</g>")

    # gilded scrollwork arcs
    for k in range(12 + 3 * i):
        r = 60 + k * 20
        parts.append(
            f'<path class="g{k % 4}" opacity=".55" d="M{400 - r} 400A{r} {r} 0 0 {rng.choice([0, 1])} {400 + r} 400"/>'
        )
    # corner filigree: nine nested rotated squares, drawn once and reused in all
    # four corners (a literal repeat of the same ornament, which is the point)
    corner = "".join(
        f'<rect class="g{s % 4}" x="{-(12 + s * 7) / 2:.0f}" y="{-(12 + s * 7) / 2:.0f}" '
        f'width="{12 + s * 7}" height="{12 + s * 7}" transform="rotate({s * 10 + i * 5})"/>'
        for s in range(9)
    )
    parts.append(f'<g id="c" transform="translate(90 90)">{corner}</g>')
    for cx, cy in ((710, 90), (90, 710), (710, 710)):
        parts.append(f'<use href="#c" transform="translate({cx - 90} {cy - 90})"/>')

    # a final beaded border
    for b in range(72):
        a = 2 * math.pi * b / 72
        parts.append(
            f'<circle class="b{b % 4}" cx="{400 + 386 * math.cos(a):.0f}" '
            f'cy="{400 + 386 * math.sin(a):.0f}"/>'
        )
    return page(ground, "".join(parts), css)


# --------------------------------------------------------------------------- #
# 3. nihilist - broken grid, glitch, clashing colors, deliberately wrong
# --------------------------------------------------------------------------- #
def nihilist(i: int) -> str:
    rng = random.Random(3000 + i)
    ground = ["#101014", "#1b1206", "#06181b", "#160c18"][i - 1]
    clash = ["#ff2d55", "#00ff9c", "#ffe600", "#7a00ff", "#00e5ff", "#ff6a00", "#c9ff00"]
    parts = [f'<rect width="800" height="800" fill="{ground}"/>']

    # a grid that fails: cells slip out of alignment and some are simply missing
    cols = 6 + i
    cell = 800 / cols
    for r in range(cols):
        for c in range(cols):
            if rng.random() < 0.28:  # holes
                continue
            dx = rng.randrange(-26, 26)
            dy = rng.randrange(-26, 26)
            col = clash[rng.randrange(len(clash))]
            parts.append(
                f'<rect x="{c * cell + dx:.0f}" y="{r * cell + dy:.0f}" '
                f'width="{cell * rng.uniform(0.35, 1.15):.0f}" height="{cell * rng.uniform(0.2, 1.1):.0f}" '
                f'fill="{col}" opacity="{rng.uniform(0.25, 0.95):.2f}"/>'
            )
    # scanline tearing
    for k in range(18 + 6 * i):
        y = rng.randrange(0, 800)
        h = rng.randrange(2, 14)
        x = rng.randrange(-120, 200)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{rng.randrange(300, 900)}" height="{h}" '
            f'fill="{clash[rng.randrange(len(clash))]}" opacity="0.7"/>'
        )
    # a diagonal that ignores the grid entirely
    parts.append(
        f'<line x1="{rng.randrange(-50, 200)}" y1="820" x2="{rng.randrange(600, 900)}" y2="-20" '
        f'stroke="{clash[i % len(clash)]}" stroke-width="{6 + i * 2}" opacity="0.85"/>'
    )
    # one deliberately half-off-canvas shape
    parts.append(
        f'<rect x="{rng.randrange(620, 780)}" y="{rng.randrange(-60, 40)}" width="240" height="240" '
        f'fill="none" stroke="{clash[(i + 3) % len(clash)]}" stroke-width="9"/>'
    )
    return page(ground, "".join(parts))


# --------------------------------------------------------------------------- #
# 4. ancestor - stained-glass panels, earth tones, leaded figures
# --------------------------------------------------------------------------- #
def ancestor(i: int) -> str:
    rng = random.Random(4000 + i)
    ground = "#1a1109"
    lead = "#241a10"
    earth = ["#8c5a2b", "#c08a3e", "#6b4226", "#a3703a", "#d9b678", "#5c3a1e", "#8a6a3c", "#b8863b"]
    parts = [f'<rect width="800" height="800" fill="{ground}"/>']

    # arched panel frame
    parts.append(
        f'<path d="M 120 760 L 120 320 A 280 280 0 0 1 680 320 L 680 760 Z" '
        f'fill="{earth[(i + 2) % len(earth)]}" stroke="{lead}" stroke-width="14"/>'
    )
    # glass shards filling the arch, leaded
    rows, cols = 9 + i, 6
    for r in range(rows):
        for c in range(cols):
            x = 120 + c * (560 / cols)
            y = 300 + r * (460 / rows)
            if y < 320 and abs(x + 46 - 400) > 240:
                continue
            w = 560 / cols
            h = 460 / rows
            parts.append(
                f'<polygon points="{x:.0f},{y:.0f} {x + w:.0f},{y + rng.randrange(-8, 8):.0f} '
                f'{x + w:.0f},{y + h:.0f} {x:.0f},{y + h + rng.randrange(-8, 8):.0f}" '
                f'fill="{earth[rng.randrange(len(earth))]}" stroke="{lead}" stroke-width="4"/>'
            )
    # a standing figure, built from leaded shapes: head, shoulders, robe
    fx = 400
    parts.append(f'<circle cx="{fx}" cy="330" r="{52 + i * 4}" fill="{earth[i % len(earth)]}" stroke="{lead}" stroke-width="9"/>')
    parts.append(
        f'<path d="M {fx - 130} 720 L {fx - 70} 420 Q {fx} 380 {fx + 70} 420 L {fx + 130} 720 Z" '
        f'fill="{earth[(i + 4) % len(earth)]}" stroke="{lead}" stroke-width="9"/>'
    )
    # arms, angled differently per seed
    tilt = 18 + i * 12
    parts.append(
        f'<path d="M {fx - 70} 450 L {fx - 190} {450 + tilt}" stroke="{lead}" stroke-width="16" fill="none"/>'
        f'<path d="M {fx + 70} 450 L {fx + 190} {450 + tilt}" stroke="{lead}" stroke-width="16" fill="none"/>'
    )
    # halo rays
    for k in range(10 + i * 2):
        a = math.pi * k / (10 + i * 2) - math.pi
        parts.append(
            f'<line x1="{fx + 66 * math.cos(a):.0f}" y1="{330 + 66 * math.sin(a):.0f}" '
            f'x2="{fx + 120 * math.cos(a):.0f}" y2="{330 + 120 * math.sin(a):.0f}" '
            f'stroke="{earth[(k + i) % len(earth)]}" stroke-width="6"/>'
        )
    parts.append(
        f'<path d="M 120 760 L 120 320 A 280 280 0 0 1 680 320 L 680 760 Z" '
        f'fill="none" stroke="{lead}" stroke-width="18"/>'
    )
    return page(ground, "".join(parts))


# --------------------------------------------------------------------------- #
# 5. futurist - starfield / machine grid, cyan and steel, hard angles
# --------------------------------------------------------------------------- #
def futurist(i: int) -> str:
    rng = random.Random(5000 + i)
    ground = "#05080d"
    cyan = "#31e6ff"
    steel = "#8aa0b4"
    pale = "#dff6ff"
    css = (
        f".st{{stroke:{pale};stroke-linecap:round;fill:none}}"
        f".gr{{stroke:{steel};stroke-width:1;opacity:.45}}"
        f".hz{{stroke:{cyan};stroke-width:1;opacity:.4}}"
        f".tk{{stroke:{cyan};stroke-width:1.6;opacity:.8}}"
    )
    parts = [f'<rect width="800" height="800" fill="{ground}"/>']

    # starfield: three dot sizes, each batched into a single zero-length path so
    # 300 stars cost ~10 chars apiece instead of ~70
    for width, count, op in ((1.4, 90 + i * 20, 0.55), (2.2, 50 + i * 12, 0.8), (3.4, 18 + i * 5, 1.0)):
        d = "".join(f"M{rng.randrange(0, 800)} {rng.randrange(0, 800)}h.1" for _ in range(count))
        parts.append(f'<path class="st" stroke-width="{width}" opacity="{op}" d="{d}"/>')

    # perspective machine grid converging on a vanishing point
    vx, vy = 400, 300 + i * 25
    rays = "".join(f"M{400 + k * 90} 800L{vx} {vy}" for k in range(-9, 10))
    parts.append(f'<path class="gr" d="{rays}"/>')
    horizons = "".join(
        f"M0 {vy + (800 - vy) * (k / 12) ** 2.1:.0f}H800" for k in range(1, 13)
    )
    parts.append(f'<path class="hz" d="{horizons}"/>')

    # hard-angled machine silhouette, different chassis per seed
    span = 120 + i * 30
    parts.append(
        f'<polygon points="{vx - span},{vy + 40} {vx},{vy - 150 - i * 20} {vx + span},{vy + 40} '
        f'{vx + span // 2},{vy + 90} {vx - span // 2},{vy + 90}" fill="none" '
        f'stroke="{cyan}" stroke-width="3"/>'
    )
    for k in range(4 + i):
        s = span - k * (span // (5 + i))
        parts.append(
            f'<polygon points="{vx - s},{vy + 30} {vx},{vy - 110 - i * 14} {vx + s},{vy + 30}" '
            f'fill="none" stroke="{steel}" stroke-width="1.4" opacity="0.7"/>'
        )
    # instrument ticks along the horizon: hard, regular, machined
    ticks = "".join(f"M{8 + k * 16.5:.0f} {vy}v-{10 if k % 4 else 24}" for k in range(48))
    parts.append(f'<path class="tk" fill="none" d="{ticks}"/>')
    return page(ground, "".join(parts), css)


# --------------------------------------------------------------------------- #
# 6. control - the legacy seed_art() geometry, text removed (no-words rule)
# --------------------------------------------------------------------------- #
CONTROL_COLORS = ["#74b86a", "#64c9e8", "#ef8354", "#d5bf55"]


def control(i: int) -> str:
    """Byte-for-byte the legacy seed_art() template minus its <h1>/<p> text nodes.

    Same circle, same two rotated inner squares, same glow, same per-religion
    colour. Only the words are gone, because --no-words applies to every world.
    """
    color = CONTROL_COLORS[i - 1]
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#090b10;color:{color};font-family:Georgia,serif}}
body{{display:grid;place-items:center}} .field{{width:72vmin;height:72vmin;border:2px solid {color};border-radius:50%;display:grid;place-items:center;box-shadow:0 0 80px {color}55;position:relative}}
.field:before,.field:after{{content:"";position:absolute;inset:12%;border:1px solid {color}99;transform:rotate(45deg)}}
.field:after{{inset:27%;transform:rotate(22.5deg);background:{color}18}}
</style></head><body><div class="field"></div></body></html>"""


BUILDERS = {
    "ascetic": ascetic,
    "baroque": baroque,
    "nihilist": nihilist,
    "ancestor": ancestor,
    "futurist": futurist,
    "control": control,
}


def build_all() -> dict[str, str]:
    """Return {relative_path: html} for all 24 files without writing anything."""
    return {
        f"{world}/seed-{i}.html": BUILDERS[world](i)
        for world in WORLDS
        for i in (1, 2, 3, 4)
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print sizes, write nothing")
    args = ap.parse_args()

    GREEN, YELLOW, RED, RESET = "\033[32m", "\033[33m", "\033[31m", "\033[0m"
    failures = 0
    for rel, art in build_all().items():
        size = len(art)
        flag = f"{GREEN}ok{RESET}" if size <= MAX_CHARS else f"{RED}TOO BIG{RESET}"
        if size > MAX_CHARS:
            failures += 1
        print(f"  {rel:<26} {size:>6} chars  {flag}")
        if not args.dry_run:
            path = OUT_ROOT / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".html.tmp")
            tmp.write_text(art)
            tmp.replace(path)
    where = "would write" if args.dry_run else "wrote"
    print(f"{YELLOW}{where}{RESET} 24 files under {OUT_ROOT}")
    if failures:
        raise SystemExit(f"{failures} file(s) over {MAX_CHARS} chars")


if __name__ == "__main__":
    main()
