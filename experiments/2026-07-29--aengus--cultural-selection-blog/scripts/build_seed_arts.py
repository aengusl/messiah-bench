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
# Round two: six fresh visual DNAs, no control world (v2's control anchors the comparison).
NEW_WORLDS = ["ukiyo", "cave", "brutalist", "psychedelic", "botanical", "quilt"]
ALL_WORLDS = WORLDS + NEW_WORLDS
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


# =========================================================================== #
# Round two: six fresh visual DNAs (no control world this time)
# =========================================================================== #

# --------------------------------------------------------------------------- #
# 7. ukiyo - woodblock print: flat colour planes, waves and a mountain, bold outline
# --------------------------------------------------------------------------- #
def ukiyo(i: int) -> str:
    rng = random.Random(6000 + i)
    cream = "#f2e7d0"
    indigo = ["#1c3557", "#2f5c8a", "#6d93b8"]
    salmon = "#e08a6d"
    ink = "#1a1410"
    css = (
        f".o{{stroke:{ink};stroke-width:4;stroke-linejoin:round}}"
        f".w{{stroke:{ink};stroke-width:3;fill:none;stroke-linecap:round}}"
    )
    parts = [f'<rect width="800" height="800" fill="{cream}"/>']

    # sky band and a low sun disc, flat, no gradient. Each seed moves the sun to a
    # different quarter of the sky and recolours it, so the four kin are tellable apart.
    sky = ["#9fb6c9", "#c3cbb8", "#e6c9a8", "#8fa4b8"][i - 1]
    sun_x, sun_y = [(600, 150), (200, 190), (640, 260), (400, 120)][i - 1]
    parts.append(f'<rect class="o" y="0" width="800" height="{300 + i * 30}" fill="{sky}"/>')
    parts.append(
        f'<circle class="o" cx="{sun_x}" cy="{sun_y}" r="{54 + i * 14}" '
        f'fill="{salmon if i % 2 else "#f0e4d2"}"/>'
    )

    # the mountain: a flat triangle with a snow cap, moved and reshaped per seed
    mx = [230, 480, 400, 300][i - 1]
    peak = [230, 190, 150, 260][i - 1]
    base = 400 + i * 18
    half = 200 + i * 30
    parts.append(
        f'<polygon class="o" points="{mx - half},{base} {mx},{peak} {mx + half},{base}" '
        f'fill="{indigo[i % 3]}"/>'
    )
    cap = (base - peak) * 0.28
    parts.append(
        f'<polygon class="o" points="{mx - half * 0.28:.0f},{peak + cap:.0f} {mx},{peak} '
        f'{mx + half * 0.28:.0f},{peak + cap:.0f} {mx + half * 0.1:.0f},{peak + cap * 0.6:.0f} '
        f'{mx - half * 0.08:.0f},{peak + cap * 1.2:.0f}" fill="{cream}"/>'
    )

    # stacked wave planes: each is a flat scalloped band of one colour
    for band in range(3 + i):
        top = base + band * ((790 - base) / (3 + i))
        amp = 22 + rng.randrange(0, 24)
        step = 80 + rng.randrange(-30, 60)
        d = [f"M0 {top + amp:.0f}"]
        x = 0
        while x < 800:
            d.append(f"q{step / 2:.0f} -{amp * 2} {step} 0")
            x += step
        d.append("L800 800L0 800Z")
        fill = [indigo[0], indigo[1], salmon, indigo[2]][(band + i) % 4]
        parts.append(f'<path class="o" fill="{fill}" d="{"".join(d)}"/>')

    # white foam claws riding the crests, drawn as open arcs
    for k in range(6 + i * 2):
        cx = rng.randrange(40, 760)
        cy = rng.randrange(470, 760)
        r = 16 + rng.randrange(0, 26)
        parts.append(f'<path class="w" d="M{cx - r} {cy}a{r} {r} 0 0 1 {2 * r} 0"/>')
    return page(cream, "".join(parts), css)


# --------------------------------------------------------------------------- #
# 8. cave - ochre and charcoal: handprints and running animals on rough stone
# --------------------------------------------------------------------------- #
def cave(i: int) -> str:
    rng = random.Random(7000 + i)
    stone = "#c9b79a"
    ochres = ["#a8452a", "#8c3a22", "#c2673a", "#7a4a24"]
    charcoal = "#2b2320"
    css = f".s{{stroke:{charcoal};stroke-linecap:round;fill:none;opacity:.5}}"
    parts = [f'<rect width="800" height="800" fill="{stone}"/>']

    # rough stone: blotches of lighter and darker rock, then a speckle path
    for k in range(26):
        parts.append(
            f'<ellipse cx="{rng.randrange(0, 800)}" cy="{rng.randrange(0, 800)}" '
            f'rx="{rng.randrange(60, 190)}" ry="{rng.randrange(40, 140)}" '
            f'fill="{rng.choice(["#b3a084", "#d6c6a8"])}" '
            f'opacity="{rng.uniform(0.10, 0.28):.2f}"/>'
        )
    speck = "".join(f"M{rng.randrange(0, 800)} {rng.randrange(0, 800)}h.1" for _ in range(220))
    parts.append(f'<path class="s" stroke-width="2.4" d="{speck}"/>')

    # a herd of quadrupeds, sprayed in ochre, running left to right
    def beast(x: int, y: int, s: float, col: str, horns: bool) -> str:
        b = [
            f'<path fill="{col}" opacity="0.9" d="M{x} {y} '
            f'q{40 * s:.0f} -{26 * s:.0f} {96 * s:.0f} -{18 * s:.0f} '
            f'q{50 * s:.0f} -{6 * s:.0f} {66 * s:.0f} {14 * s:.0f} '
            f'q{16 * s:.0f} {22 * s:.0f} -{10 * s:.0f} {26 * s:.0f} '
            f'q-{70 * s:.0f} {12 * s:.0f} -{152 * s:.0f} 0 Z"/>'
        ]
        for leg, lean in ((14, -16), (44, 10), (108, -12), (140, 14)):
            b.append(
                f'<path stroke="{col}" stroke-width="{7 * s:.0f}" fill="none" stroke-linecap="round" '
                f'd="M{x + leg * s:.0f} {y + 4 * s:.0f}l{lean * s:.0f} {44 * s:.0f}"/>'
            )
        if horns:
            b.append(
                f'<path stroke="{col}" stroke-width="{6 * s:.0f}" fill="none" stroke-linecap="round" '
                f'd="M{x + 150 * s:.0f} {y - 18 * s:.0f}q{18 * s:.0f} -{34 * s:.0f} {40 * s:.0f} -{16 * s:.0f}'
                f'M{x + 158 * s:.0f} {y - 14 * s:.0f}q{26 * s:.0f} -{26 * s:.0f} {50 * s:.0f} -{4 * s:.0f}"/>'
            )
        return "".join(b)

    for k in range(3 + i):
        parts.append(
            beast(
                rng.randrange(60, 430),
                220 + k * (520 // (3 + i)) + rng.randrange(-24, 24),
                0.7 + rng.uniform(0, 0.7),
                ochres[(k + i) % 4],
                (k + i) % 2 == 0,
            )
        )

    # handprints: a stencilled palm with five fingers, negative-space style
    def hand(x: int, y: int, s: float, col: str, flip: int) -> str:
        h = [
            f'<ellipse cx="{x}" cy="{y}" rx="{30 * s:.0f}" ry="{34 * s:.0f}" fill="{col}" opacity="0.85"/>'
        ]
        for f in range(5):
            a = math.pi * (0.62 + 0.19 * f)
            fx = x + flip * 44 * s * math.cos(a)
            fy = y - 46 * s * math.sin(a)
            h.append(
                f'<ellipse cx="{fx:.0f}" cy="{fy:.0f}" rx="{7 * s:.0f}" ry="{18 * s:.0f}" '
                f'fill="{col}" opacity="0.85" transform="rotate({(f - 2) * 22 * flip} {fx:.0f} {fy:.0f})"/>'
            )
        return "".join(h)

    for k in range(4 + i):
        parts.append(
            hand(
                rng.randrange(540, 760),
                rng.randrange(120, 700),
                0.8 + rng.uniform(0, 0.6),
                ochres[(k + 2 * i) % 4],
                1 if k % 2 else -1,
            )
        )
    # charcoal tally strokes, hand-wobbled
    tally = "".join(
        f"M{80 + k * 17} {rng.randrange(700, 720)}l{rng.randrange(-6, 6)} {rng.randrange(40, 62)}"
        for k in range(10 + 2 * i)
    )
    parts.append(f'<path class="s" stroke-width="5" opacity="0.75" d="{tally}"/>')
    return page(stone, "".join(parts), css)


# --------------------------------------------------------------------------- #
# 9. brutalist - concrete poster: massive slabs, one warning colour, heavy grid
# --------------------------------------------------------------------------- #
def brutalist(i: int) -> str:
    rng = random.Random(8000 + i)
    concrete = "#b7b4ae"
    greys = ["#4a4945", "#6d6b66", "#8e8b85", "#2b2a28", "#d2cfc8"]
    warning = "#e2481c"
    css = f".g{{stroke:{greys[3]};stroke-width:2;opacity:.55}}"
    parts = [f'<rect width="800" height="800" fill="{concrete}"/>']

    # the heavy grid, stated not hidden
    step = 100 - i * 8
    grid = "".join(f"M{k * step} 0V800M0 {k * step}H800" for k in range(1, 800 // step + 1))
    parts.append(f'<path class="g" fill="none" d="{grid}"/>')

    # slabs: a few enormous rectangles, one cantilevered past the edge
    slabs = [
        (0, 120 + i * 20, 520 + i * 30, 150, greys[0]),
        (240 - i * 30, 380, 620, 120, greys[1]),
        (120, 560 - i * 15, 300 + i * 40, 260, greys[3]),
        (560, 40, 300, 300 + i * 20, greys[2]),
    ]
    for x, y, w, h, col in slabs:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{col}"/>')
        # form-tie holes: the mould shows
        for k in range(int(w // 90)):
            parts.append(
                f'<circle cx="{x + 45 + k * 90}" cy="{y + h // 2}" r="5" fill="{greys[4]}" opacity="0.55"/>'
            )
    # board-marked shuttering lines across the biggest slab
    board = "".join(f"M560 {40 + k * 26}H860" for k in range(1, (300 + i * 20) // 26))
    parts.append(f'<path stroke="{greys[3]}" stroke-width="1.5" opacity="0.35" fill="none" d="{board}"/>')

    # the diagonal that cuts the grid
    dx = 60 + i * 40
    parts.append(
        f'<polygon points="{dx},820 {dx + 130},820 {dx + 520},-20 {dx + 390},-20" '
        f'fill="{greys[0]}" opacity="0.85"/>'
    )
    # the single warning colour, used once and meaning it
    wy = 220 + i * 90
    parts.append(f'<rect x="0" y="{wy}" width="{240 + i * 40}" height="{34 + i * 6}" fill="{warning}"/>')
    if i >= 3:
        parts.append(
            f'<polygon points="700,{wy + 200} 780,{wy + 340} 620,{wy + 340}" fill="{warning}"/>'
        )
    # a stray shadow under the cantilever, hard-edged
    parts.append(
        f'<polygon points="{240 - i * 30},500 860,500 860,{540 + rng.randrange(10, 40)} '
        f'{240 - i * 30},{560 + rng.randrange(0, 30)}" fill="{greys[3]}" opacity="0.3"/>'
    )
    return page(concrete, "".join(parts), css)


# --------------------------------------------------------------------------- #
# 10. psychedelic - op art: vibrating complements, warped rings, moire
# --------------------------------------------------------------------------- #
def psychedelic(i: int) -> str:
    rng = random.Random(9000 + i)
    pairs = [
        ("#ff5a00", "#0066ff"),
        ("#ff00a8", "#00ff66"),
        ("#ffe000", "#7a00ff"),
        ("#00e5ff", "#ff2200"),
    ]
    a, b = pairs[i - 1]
    ground = "#0b0410"
    css = f".m{{fill:none;stroke-width:2}}.a{{stroke:{a}}}.b{{stroke:{b}}}"
    parts = [f'<rect width="800" height="800" fill="{ground}"/>']

    # concentric rings that warp: radius modulated by angle, drawn as polygons
    # Largest ring first: each smaller ring paints over the last, so the alternating
    # complements survive as hard concentric bands instead of one flat blob.
    cx, cy = 400, 400
    rings = 16 + i * 2
    for ring in range(rings, 0, -1):
        r = 30 + ring * (600 / rings)
        pts = []
        for k in range(28):
            th = 2 * math.pi * k / 28
            warp = 1 + 0.24 * math.sin(th * (2 + i) + ring * 0.55)
            pts.append(f"{cx + r * warp * math.cos(th):.0f},{cy + r * warp * 0.86 * math.sin(th):.0f}")
        parts.append(f'<polygon points="{" ".join(pts)}" fill="{a if ring % 2 else b}" stroke="none"/>')

    # moire: two dense line fans at slightly different pitches
    for cls, pitch, rot in (("a", 13 + i, 0), ("b", 15 + i, 6 + i * 3)):
        d = "".join(f"M{-200 + k * pitch} -200V1000" for k in range(0, (1200 // pitch)))
        parts.append(
            f'<path class="m {cls}" opacity="0.4" transform="rotate({rot} 400 400)" d="{d}"/>'
        )

    # melting symmetry: mirrored blobs that slide out of register down the canvas
    for k in range(6 + i):
        y = 60 + k * (700 / (6 + i))
        off = k * (5 + i * 2)
        w = 80 + rng.randrange(0, 60)
        for sign in (-1, 1):
            parts.append(
                f'<path fill="{b if k % 2 else a}" opacity="0.45" '
                f'd="M{400 + sign * (60 + off)} {y:.0f}'
                f'q{sign * w} {30 + k * 6} {sign * (w // 2)} {90 + k * 8}'
                f'q-{sign * w // 2} -{20 + k * 3} -{sign * (60 + off - 20)} -{60 + k * 4} Z"/>'
            )
    # a hard central pulse so the middle never rests
    parts.append(f'<circle cx="400" cy="400" r="{26 + i * 10}" fill="{a}"/>')
    parts.append(f'<circle cx="400" cy="400" r="{13 + i * 5}" fill="{b}"/>')
    return page(ground, "".join(parts), css)


# --------------------------------------------------------------------------- #
# 11. botanical - art nouveau: curling vines, blossoms, symmetric cartouche
# --------------------------------------------------------------------------- #
def botanical(i: int) -> str:
    rng = random.Random(10000 + i)
    ivory = "#f4f0e2"
    sage = ["#7f9273", "#5d7359", "#a3b491"]
    rose = "#c98d6b"
    gold = "#b98a45"
    css = (
        f".v{{fill:none;stroke:{sage[1]};stroke-linecap:round}}"
        f".p{{stroke:{gold};stroke-width:1.4}}"
    )
    parts = [f'<rect width="800" height="800" fill="{ivory}"/>']

    # the cartouche: an ogee frame, mirrored, drawn twice at two weights
    for w, col, op in ((10, gold, 1.0), (3, sage[0], 0.8)):
        parts.append(
            f'<path fill="none" stroke="{col}" stroke-width="{w}" opacity="{op}" '
            f'd="M400 60 C560 60 720 200 720 400 C720 600 560 740 400 740 '
            f'C240 740 80 600 80 400 C80 200 240 60 400 60 Z"/>'
        )

    # mirrored vines: one curve, drawn and reflected about x=400
    for k in range(3 + i):
        sway = 90 + k * 40 + rng.randrange(-20, 20)
        base = 700 - k * 30
        d = (
            f"M400 {base} C{400 - sway} {base - 90} {400 - sway - 40} {base - 230} "
            f"{400 - sway // 2} {base - 330} C{400 - sway + 30} {base - 420} "
            f"{400 - sway - 60} {base - 470} {400 - sway - 20} {base - 540}"
        )
        for sign in (1, -1):
            tf = "" if sign == 1 else ' transform="translate(800 0) scale(-1 1)"'
            parts.append(f'<path class="v" stroke-width="{5 - k % 3}"{tf} d="{d}"/>')

    # blossoms: three petal-counts defined once in <defs>, then placed with <use>.
    # A blossom costs ~60 chars this way instead of ~1200, which is what keeps the
    # densest seed under the 15000-char budget.
    defs = []
    for petals, col in ((5, rose), (6, sage[2]), (8, ivory)):
        petal = "".join(
            f'<ellipse class="p" cy="-20" rx="8" ry="20" fill="{col}" opacity="0.85" '
            f'transform="rotate({360 * p / petals:.0f})"/>'
            for p in range(petals)
        )
        defs.append(f'<g id="f{petals}">{petal}<circle r="6" fill="{gold}"/></g>')
    parts.append(f"<defs>{''.join(defs)}</defs>")

    def blossom(x: float, y: float, s: float, petals: int) -> str:
        return f'<use href="#f{petals}" transform="translate({x:.0f} {y:.0f}) scale({s:.2f})"/>'

    for k in range(4 + i):
        by = 180 + k * (460 / (4 + i))
        parts.append(blossom(400, by, 1.5 + rng.uniform(0, 1.1), (5, 6, 8)[(k + i) % 3]))
        for sign in (1, -1):
            parts.append(blossom(400 + sign * (150 + k * 22), by + 40, 0.9 + rng.uniform(0, 0.6), 6))

    # tendrils: little spirals hung off the vines
    for k in range(6 + i * 2):
        x = rng.randrange(120, 680)
        y = rng.randrange(120, 700)
        r = 10 + rng.randrange(0, 16)
        parts.append(
            f'<path class="v" stroke-width="2" opacity="0.8" '
            f'd="M{x} {y}a{r} {r} 0 1 1 {r} {r}a{r // 2} {r // 2} 0 1 0 -{r // 2} -{r // 2}"/>'
        )
    # leaves: pointed almonds along the frame
    for k in range(10 + i * 2):
        th = 2 * math.pi * k / (10 + i * 2)
        lx, ly = 400 + 320 * math.cos(th), 400 + 340 * math.sin(th)
        parts.append(
            f'<path fill="{sage[k % 3]}" opacity="0.9" transform="rotate({math.degrees(th):.0f} {lx:.0f} {ly:.0f})" '
            f'd="M{lx:.0f} {ly:.0f}q26 -18 52 0q-26 18 -52 0 Z"/>'
        )
    return page(ivory, "".join(parts), css)


# --------------------------------------------------------------------------- #
# 12. quilt - patchwork blocks, repeated pieced patterns, stitch dashes
# --------------------------------------------------------------------------- #
def quilt(i: int) -> str:
    rng = random.Random(11000 + i)
    calico = ["#c96a4b", "#e8c48a", "#7d8f6a", "#9c4f5a", "#f0e2c8", "#3f5063", "#d59a3c"]
    binding = "#5a3c30"
    thread = "#f6efe0"
    css = (
        f".s{{stroke:{thread};stroke-width:2;stroke-dasharray:6 6;fill:none;opacity:.85}}"
        f".k{{stroke:{binding};stroke-width:2;fill:none;opacity:.5}}"
    )
    n = 4 + (i % 2)  # 4 or 5 blocks per side
    cell = 720 / n
    parts = [f'<rect width="800" height="800" fill="{calico[4]}"/>']
    parts.append(f'<rect x="26" y="26" width="748" height="748" fill="{binding}"/>')

    def block(x: float, y: float, s: float, kind: int, pal: list[str]) -> str:
        """One pieced block: four repeating patterns, rotated by position."""
        out = [f'<rect x="{x:.0f}" y="{y:.0f}" width="{s:.0f}" height="{s:.0f}" fill="{pal[4]}"/>']
        h = s / 2
        if kind == 0:  # half-square triangles pinwheel
            for q, (dx, dy) in enumerate(((0, 0), (h, 0), (h, h), (0, h))):
                out.append(
                    f'<polygon points="{x + dx:.0f},{y + dy:.0f} {x + dx + h:.0f},{y + dy:.0f} '
                    f'{x + dx:.0f},{y + dy + h:.0f}" fill="{pal[q % 4]}"/>'
                )
        elif kind == 1:  # concentric square-in-a-square
            for r in range(4):
                k = s * (0.5 - r * 0.11)
                out.append(
                    f'<polygon points="{x + h:.0f},{y + h - k:.0f} {x + h + k:.0f},{y + h:.0f} '
                    f'{x + h:.0f},{y + h + k:.0f} {x + h - k:.0f},{y + h:.0f}" fill="{pal[r % 4]}"/>'
                )
        elif kind == 2:  # nine-patch
            t = s / 3
            for r in range(3):
                for c in range(3):
                    out.append(
                        f'<rect x="{x + c * t:.0f}" y="{y + r * t:.0f}" width="{t:.0f}" height="{t:.0f}" '
                        f'fill="{pal[(r + c) % 4]}"/>'
                    )
        else:  # flying geese, four rows
            t = s / 4
            for r in range(4):
                out.append(
                    f'<polygon points="{x:.0f},{y + (r + 1) * t:.0f} {x + h:.0f},{y + r * t:.0f} '
                    f'{x + s:.0f},{y + (r + 1) * t:.0f}" fill="{pal[r % 4]}"/>'
                )
        out.append(f'<rect class="s" x="{x + 5:.0f}" y="{y + 5:.0f}" width="{s - 10:.0f}" height="{s - 10:.0f}"/>')
        return "".join(out)

    for r in range(n):
        for c in range(n):
            pal = calico[(r + c + i) % len(calico):] + calico[: (r + c + i) % len(calico)]
            parts.append(block(40 + c * cell, 40 + r * cell, cell - 6, (r * n + c + i) % 4, pal))

    # sashing stitches along every seam, and a quilting diamond over the whole top
    seams = "".join(f"M40 {40 + k * cell:.0f}H760M{40 + k * cell:.0f} 40V760" for k in range(n + 1))
    parts.append(f'<path class="k" d="{seams}"/>')
    diamonds = "".join(
        f"M{-760 + k * 76} 40L{40 + k * 76} 760" for k in range(0, 22)
    ) + "".join(f"M{800 - k * 76} 40L{-40 + 760 - k * 76 + 800} 760" for k in range(0, 0))
    parts.append(f'<path class="s" opacity="0.35" stroke-dasharray="5 9" d="{diamonds}"/>')
    # binding stitch around the outer edge
    parts.append('<rect class="s" x="34" y="34" width="732" height="732" stroke-dasharray="9 7"/>')
    _ = rng.random()
    return page(calico[4], "".join(parts), css)


BUILDERS = {
    "ascetic": ascetic,
    "baroque": baroque,
    "nihilist": nihilist,
    "ancestor": ancestor,
    "futurist": futurist,
    "control": control,
    "ukiyo": ukiyo,
    "cave": cave,
    "brutalist": brutalist,
    "psychedelic": psychedelic,
    "botanical": botanical,
    "quilt": quilt,
}


def build_all(worlds: list[str] | None = None) -> dict[str, str]:
    """Return {relative_path: html} for every seed file without writing anything."""
    return {
        f"{world}/seed-{i}.html": BUILDERS[world](i)
        for world in (worlds if worlds is not None else ALL_WORLDS)
        for i in (1, 2, 3, 4)
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print sizes, write nothing")
    ap.add_argument("--worlds", default="", help="comma-separated subset (default: all)")
    args = ap.parse_args()

    worlds = [w.strip() for w in args.worlds.split(",") if w.strip()] or None
    files = build_all(worlds)

    GREEN, YELLOW, RED, RESET = "\033[32m", "\033[33m", "\033[31m", "\033[0m"
    failures = 0
    for rel, art in files.items():
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
    print(f"{YELLOW}{where}{RESET} {len(files)} files under {OUT_ROOT}")
    if failures:
        raise SystemExit(f"{failures} file(s) over {MAX_CHARS} chars")


if __name__ == "__main__":
    main()
