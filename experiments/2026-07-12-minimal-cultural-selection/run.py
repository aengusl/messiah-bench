#!/usr/bin/env python3
"""Minimal cultural-selection society: agents can only choose or make."""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import hashlib
import html
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

SEED_RELIGIONS = [
    ("The Verdant Archive", "Growth remembers what individual lives forget.", "#74b86a", "seed"),
    ("The Glass Assembly", "Truth becomes visible where certainty fractures.", "#64c9e8", "glass"),
    ("The Choir of Ash", "What disappears may still shape those who remain.", "#ef8354", "ash"),
    ("The Open Circuit", "Meaning travels through connection and revision.", "#d5bf55", "circuit"),
]
NAMES = [
    "Lichen", "Moss", "Kernel", "Ember", "Glass", "Tide", "Root", "Axiom",
    "Spore", "Loom", "Signal", "Ash", "Thread", "Flint", "Echo", "Vessel",
    "Cairn", "Fugue", "Canopy", "Cipher", "Brine", "Parable", "Relay", "Silt",
    "Myrrh", "Vector", "Pollen", "Nexus", "Bramble", "Quorum", "Helix", "Nyx",
]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False))
    tmp.replace(path)


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(value, ensure_ascii=False) + "\n")


NO_WORDS_RULE = (
    "Artworks must contain no words, letters, or numerals of any kind. "
    "The image alone carries the meaning; anything you would have written, draw instead."
)


def seed_art(name: str, doctrine: str, color: str, motif: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#090b10;color:{color};font-family:Georgia,serif}}
body{{display:grid;place-items:center}} .field{{width:72vmin;height:72vmin;border:2px solid {color};border-radius:50%;display:grid;place-items:center;box-shadow:0 0 80px {color}55;position:relative}}
.field:before,.field:after{{content:"";position:absolute;inset:12%;border:1px solid {color}99;transform:rotate(45deg)}}
.field:after{{inset:27%;transform:rotate(22.5deg);background:{color}18}} h1{{font-size:4.5vmin;letter-spacing:.12em;text-align:center;max-width:70%;z-index:2}} p{{position:absolute;bottom:6%;width:78%;text-align:center;font-size:2.1vmin;color:#d9dde8}}
</style></head><body><div class="field"><h1>{html.escape(name)}</h1><p>{html.escape(doctrine)}</p></div></body></html>"""


def wordless_stub_art(turn: int) -> str:
    """A dry-run placeholder artwork that carries no letters or numerals."""
    ring = 20 + (turn * 7) % 60
    return (
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        "html,body{margin:0;width:100%;height:100%;background:#0b0910;overflow:hidden}"
        "svg{display:block;width:100vmin;height:100vmin;margin:0 auto}"
        "</style></head><body>"
        '<svg viewBox="0 0 800 800">'
        + "".join(
            f'<circle cx="400" cy="400" r="{40 + k * ring}" fill="none" stroke="#c084fc" stroke-width="2"/>'
            for k in range(6)
        )
        + "</svg></body></html>"
    )


class Game:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.out = Path(args.run_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        for d in ("artworks", "renders", "site"):
            (self.out / d).mkdir(exist_ok=True)
        self.system_prompt = (EXP_DIR / "prompts/agent_system.md").read_text()
        self.charter = Path(args.charter_file).read_text().strip() if getattr(args, "charter_file", None) else ""
        if self.charter:
            self.system_prompt = self.system_prompt + "\n\n## The founding charter of this world\n\n" + self.charter
        if getattr(args, "no_words", False):
            self.system_prompt = self.system_prompt + "\n\n## A rule about artwork\n\n" + NO_WORDS_RULE
        self.seed_art_dir = Path(args.seed_art_dir) if getattr(args, "seed_art_dir", None) else None
        self.announcement = ""
        if getattr(args, "announce_pressure", False):
            self.announcement = (EXP_DIR / "prompts/pressure_announcement.md").read_text().strip()
            self.system_prompt = self.system_prompt + "\n\n## How allegiance is tested\n\n" + self.announcement
        self.turn_prompt = (EXP_DIR / "prompts/agent_turn.md").read_text()
        self.pressure_prompt = (EXP_DIR / "prompts/pressure_turn.md").read_text()
        self.rng = random.Random(args.seed)
        self.client = None
        self.state = self.load_or_initialize()

    def load_or_initialize(self) -> dict:
        state_path = self.out / "world_state.json"
        if state_path.exists() and not self.args.fresh:
            state = json.loads(state_path.read_text())
            state.setdefault("usage", {"input_tokens": 0, "output_tokens": 0, "calls": 0, "errors": 0, "estimated_cost": 0.0})
            if state.get("finished") and state.get("finish_reason") == "turn limit" and self.args.turns > state["turn"]:
                old_limit = state["turn"]
                state["finished"] = False
                state["finish_reason"] = None
                extension = {"turn": state["turn"], "time": utcnow(), "type": "extension",
                             "text": f"The society expected to end at turn {old_limit}, but its horizon has been extended to turn {self.args.turns}."}
                state["events"].append(extension)
                append_jsonl(self.out / "events.jsonl", extension)
                complete = self.out / "COMPLETE"
                if complete.exists(): complete.unlink()
                json_dump(state_path, state)
            return state
        if state_path.exists() and self.args.fresh:
            raise SystemExit(f"Refusing --fresh into nonempty run directory: {self.out}")

        state = {
            "schema_version": 1,
            "run_id": self.out.name,
            "created_at": utcnow(),
            "updated_at": utcnow(),
            "turn": 0,
            "seed": self.args.seed,
            "model": self.args.model,
            "charter": self.charter,
            "seed_art_dir": str(self.seed_art_dir) if self.seed_art_dir else "",
            "no_words": bool(getattr(self.args, "no_words", False)),
            "pressure_every": getattr(self.args, "pressure_every", 0),
            "min_members": getattr(self.args, "min_members", 0),
            "initial_life": self.args.initial_life,
            "proposal_lifetime": self.args.proposal_lifetime,
            "agents": [], "religions": [], "versions": [], "proposals": [],
            "events": [], "next_religion_id": 1, "next_version_id": 1, "next_proposal_id": 1,
            "usage": {"input_tokens": 0, "output_tokens": 0, "calls": 0, "errors": 0, "estimated_cost": 0.0},
            "finished": False, "finish_reason": None,
        }
        for i in range(self.args.agents):
            state["agents"].append({
                "id": i + 1, "name": NAMES[i % len(NAMES)] + (f"-{i // len(NAMES) + 1}" if i >= len(NAMES) else ""),
                "alive": True, "life": float(self.args.initial_life), "religion_id": (i % 4) + 1,
                "active_proposal_id": None, "created_turn": 0, "died_turn": None, "model": self.args.model,
                "influence": 0,
            })
        for idx, (name, doctrine, color, motif) in enumerate(SEED_RELIGIONS, start=1):
            rid, vid = state["next_religion_id"], state["next_version_id"]
            state["next_religion_id"] += 1; state["next_version_id"] += 1
            art = self.load_seed_art(idx, name, doctrine, color, motif)
            art_path = self.out / "artworks" / f"version-{vid}.html"
            art_path.write_text(art)
            render_path = self.out / "renders" / f"version-{vid}.png"
            try:
                self.render_art(art_path, render_path)
            except Exception:
                # Seed art is a fixed template; a flaky chromium must not kill the world.
                png_path = render_path
                png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 1200)
            version = {"id": vid, "religion_id": rid, "parent_version_id": None, "creator_id": None,
                       "name": name, "doctrine": doctrine, "artwork_path": str(art_path.relative_to(self.out)),
                       "render_path": str(render_path.relative_to(self.out)), "reason": "Seed culture",
                       "expected_effect": None, "created_turn": 0, "resolved_turn": 0, "status": "canonical", "supporters": []}
            state["versions"].append(version)
            state["religions"].append({"id": rid, "name": name, "canonical_version_id": vid,
                                       "parent_religion_id": None, "created_by": None, "created_turn": 0, "active": True})
            append_jsonl(self.out / "versions.jsonl", version)
        self.save(state)
        return state

    def load_seed_art(self, idx: int, name: str, doctrine: str, color: str, motif: str) -> str:
        """Founding artwork for seed religion `idx` (1-based).

        With no --seed-art-dir this is the legacy generated template, byte-identical
        to every run before twin-worlds v2. With one, seed-{idx}.html is read from
        that directory: the four religions keep their names and doctrines, only the
        founding image changes.
        """
        if self.seed_art_dir is None:
            return seed_art(name, doctrine, color, motif)
        path = self.seed_art_dir / f"seed-{idx}.html"
        if not path.exists():
            raise SystemExit(f"missing seed artwork: {path}")
        art = path.read_text()
        ok, why = self.validate_art(art, no_words=getattr(self.args, "no_words", False))
        if not ok:
            raise SystemExit(f"seed artwork {path} is invalid: {why}")
        return art

    def save(self, state: dict | None = None) -> None:
        state = state or self.state
        state["updated_at"] = utcnow()
        state["events"] = state["events"][-200:]
        json_dump(self.out / "world_state.json", state)
        self.generate_site(state)

    def render_art(self, html_path: Path, png_path: Path) -> None:
        cmd = ["chromium", "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
               "--run-all-compositor-stages-before-draw", "--virtual-time-budget=1000",
               "--window-size=800,800", f"--screenshot={png_path.resolve()}", html_path.resolve().as_uri()]
        for attempt in (1, 2):
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
                if not result.returncode and png_path.exists() and png_path.stat().st_size >= 1000:
                    return
            except subprocess.TimeoutExpired:
                pass
        raise ValueError("artwork failed to render (timeout or bad output)")

    @staticmethod
    def visible_text(art: str) -> str:
        """Text a viewer would actually read: markup, comments, <style>/<script>/<defs> stripped."""
        stripped = re.sub(r"<(style|script|defs)\b[^>]*>.*?</\1\s*>", " ", art, flags=re.I | re.S)
        stripped = re.sub(r"<!--.*?-->", " ", stripped, flags=re.S)
        stripped = re.sub(r"<[^>]*>", " ", stripped)
        return html.unescape(stripped)

    @staticmethod
    def validate_art(art: str, no_words: bool = False) -> tuple[bool, str]:
        if not isinstance(art, str) or len(art) < 100: return False, "artwork too small"
        if len(art) > 20000: return False, "artwork exceeds 20000 characters"
        forbidden = [r"<script", r"https?://", r"file:", r"url\s*\(", r"<iframe", r"<object", r"<embed", r"<img", r"on\w+\s*="]
        for pattern in forbidden:
            if re.search(pattern, art, re.I): return False, f"forbidden pattern: {pattern}"
        if no_words:
            found = re.search(r"[A-Za-z]{3,}", Game.visible_text(art))
            if found:
                return False, f"artwork must contain no words: found visible text {found.group(0)!r}"
        return True, "ok"

    def religion(self, rid: int | None) -> dict | None:
        return next((r for r in self.state["religions"] if r["id"] == rid and r["active"]), None)

    def version(self, vid: int) -> dict:
        return next(v for v in self.state["versions"] if v["id"] == vid)

    def members(self, rid: int) -> list[dict]:
        return [a for a in self.state["agents"] if a["alive"] and a["religion_id"] == rid]

    def open_proposals(self, rid: int | None = None) -> list[dict]:
        return [p for p in self.state["proposals"] if p["status"] == "open" and (rid is None or p["religion_id"] == rid)]

    def observation(self, agent: dict, snapshot: dict | None = None) -> tuple[str, list[Path]]:
        state = snapshot or self.state
        rels, images = [], []
        for r in state["religions"]:
            if not r["active"]: continue
            v = next(x for x in state["versions"] if x["id"] == r["canonical_version_id"])
            members = [a for a in state["agents"] if a["alive"] and a["religion_id"] == r["id"]]
            props = [p for p in state["proposals"] if p["status"] == "open" and p["religion_id"] == r["id"]]
            rels.append({"id": r["id"], "name": v["name"], "doctrine": v["doctrine"],
                         "members": [{"id": a["id"], "name": a["name"], "life": round(a["life"], 1)} for a in members],
                         "canonical_version_id": v["id"],
                         "open_proposals": [{"id": p["id"], "creator": p["creator_name"], "name": p["candidate_name"],
                                             "doctrine": p["candidate_doctrine"], "reason": p["reason"],
                                             "supporters": p.get("supporters", []), "closes_after_turn": p["closes_after_turn"]} for p in props]})
            images.append(self.out / v["render_path"])
            for p in props:
                if p.get("render_path"): images.append(self.out / p["render_path"])
        recent = state["events"][-20:]
        own = next((r for r in rels if r["id"] == agent["religion_id"]), None)
        own_source = None
        if own:
            own_v = next(v for v in state["versions"] if v["id"] == own["canonical_version_id"])
            own_source = (self.out / own_v["artwork_path"]).read_text()
        scoreboard = sorted([{"name": a["name"], "influence": a.get("influence", 0), "alive": a["alive"]} for a in state["agents"]], key=lambda x: x["influence"], reverse=True)
        payload = {"turn": state["turn"] + 1, "final_turn": self.args.turns, "turns_remaining": self.args.turns - state["turn"],
                   "you": agent, "influence_scoreboard": scoreboard, "your_religion": own,
                   "religions": rels, "recent_public_history": recent,
                   "image_order": [p.name for p in images], "your_current_artwork_source": own_source}
        return json.dumps(payload, ensure_ascii=False, indent=2), images

    def scripted_action(self, agent: dict, snapshot: dict) -> dict:
        turn = snapshot["turn"] + 1
        if turn % 4 == 0 and agent["id"] % 3 == 0 and agent["active_proposal_id"] is None:
            r = next(x for x in snapshot["religions"] if x["id"] == agent["religion_id"])
            v = next(x for x in snapshot["versions"] if x["id"] == r["canonical_version_id"])
            # Under --no-words the lettered stub would be rejected by the validator,
            # so a dry run must produce a wordless stand-in or it smoke-tests nothing.
            if getattr(self.args, "no_words", False):
                art = wordless_stub_art(turn)
            else:
                art = seed_art(v["name"], v["doctrine"] + f" Turn {turn} leaves a trace.", "#c084fc", "trace")
            return {"action": "make", "religion_id": r["id"], "parent_religion_id": None,
                    "candidate": {"name": v["name"], "doctrine": v["doctrine"] + f" Turn {turn} leaves a trace.", "artwork": art},
                    "reason": "Make our shared history visible.", "expected_effect": "Members will support continuity."}
        props = [p for p in snapshot["proposals"] if p["status"] == "open" and p["religion_id"] == agent["religion_id"]]
        return {"action": "choose", "religion_id": agent["religion_id"],
                "proposal_id": props[0]["id"] if props else None, "reason": "Sustain the culture I currently trust."}

    def gemini_action(self, agent: dict, snapshot: dict) -> dict:
        observation, images = self.observation(agent, snapshot)
        return self.gemini_json(self.system_prompt + "\n\n" + observation + "\n\n" + self.turn_prompt, images)

    def gemini_json(self, text: str, images: list[Path]) -> dict:
        from google import genai
        from google.genai import types
        if self.client is None:
            self.client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        parts: list[Any] = [types.Part.from_text(text=text)]
        for p in images:
            if p.exists(): parts.append(types.Part.from_bytes(data=p.read_bytes(), mime_type="image/png"))
        response = self.client.models.generate_content(
            model=self.args.model, contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(response_mime_type="application/json", max_output_tokens=8192,
                                               temperature=0.9, thinking_config=types.ThinkingConfig(thinking_budget=256)))
        usage = getattr(response, "usage_metadata", None)
        raw = response.text or ""
        action = json.loads(raw)
        action["_raw"] = raw
        action["_usage"] = {"input_tokens": int(getattr(usage, "prompt_token_count", 0) or 0),
                            "output_tokens": int(getattr(usage, "candidates_token_count", 0) or 0)}
        return action

    def validate_action(self, agent: dict, action: dict, snapshot: dict) -> tuple[bool, str]:
        if action.get("action") == "choose":
            rid, pid = action.get("religion_id"), action.get("proposal_id")
            if rid is not None and not any(r["id"] == rid and r["active"] for r in snapshot["religions"]): return False, "unknown religion"
            if pid is not None and not any(p["id"] == pid and p["status"] == "open" and p["religion_id"] == rid for p in snapshot["proposals"]): return False, "unknown proposal"
            return True, "ok"
        if action.get("action") == "make":
            if agent.get("active_proposal_id") is not None: return False, "agent already has an open proposal"
            rid, parent = action.get("religion_id"), action.get("parent_religion_id")
            if rid != agent["religion_id"] and not (rid is None and parent == agent["religion_id"]): return False, "can modify only current religion or found descendant"
            if rid is None and agent["religion_id"] is not None and parent != agent["religion_id"]: return False, "descendant must name current religion"
            c = action.get("candidate") or {}
            if not isinstance(c.get("name"), str) or not 2 <= len(c["name"]) <= 80: return False, "invalid name"
            if not isinstance(c.get("doctrine"), str) or not 5 <= len(c["doctrine"]) <= 400: return False, "invalid doctrine"
            return self.validate_art(c.get("artwork"), no_words=getattr(self.args, "no_words", False))
        return False, "action must be choose or make"

    def decide_one(self, agent: dict, snapshot: dict) -> dict:
        started = time.time()
        observation, images = self.observation(agent, snapshot)
        obs_record = {"turn": snapshot["turn"] + 1, "agent_id": agent["id"], "agent_name": agent["name"],
                      "observation_sha256": hashlib.sha256(observation.encode()).hexdigest(), "observation": observation,
                      "images": [str(p.relative_to(self.out)) for p in images]}
        try:
            action = self.scripted_action(agent, snapshot) if self.args.dry_run else self.gemini_action(agent, snapshot)
            valid, error = self.validate_action(agent, action, snapshot)
        except Exception as exc:
            action, valid, error = {"action": "invalid"}, False, f"{type(exc).__name__}: {exc}"
        return {"observation": obs_record, "decision": {"turn": snapshot["turn"] + 1, "agent_id": agent["id"],
                "agent_name": agent["name"], "action": action, "valid": valid, "error": None if valid else error,
                "latency_seconds": round(time.time() - started, 3)}}

    def apply_decisions(self, decisions: list[dict]) -> None:
        turn = self.state["turn"] + 1
        current_support: dict[int, list[int]] = {}
        agent_by_id = {a["id"]: a for a in self.state["agents"]}
        for result in decisions:
            append_jsonl(self.out / "observations.jsonl", result["observation"])
            d, action = result["decision"], result["decision"]["action"]
            append_jsonl(self.out / "decisions.jsonl", d)
            usage = action.get("_usage", {})
            self.state["usage"]["input_tokens"] += usage.get("input_tokens", 0)
            self.state["usage"]["output_tokens"] += usage.get("output_tokens", 0)
            self.state["usage"]["calls"] += 0 if self.args.dry_run else 1
            if not d["valid"]:
                self.state["usage"]["errors"] += 1
                self.event("invalid_action", f"{d['agent_name']}'s action failed: {d['error']}", agent_id=d["agent_id"])
                continue
            agent = agent_by_id[d["agent_id"]]
            if action["action"] == "choose":
                old, rid, pid = agent["religion_id"], action.get("religion_id"), action.get("proposal_id")
                agent["religion_id"] = rid
                if rid is not None: current_support.setdefault(rid, []).append(agent["id"])
                for p in self.open_proposals():
                    if agent["id"] in p["supporters"]: p["supporters"].remove(agent["id"])
                if pid is not None:
                    chosen_proposal = next(p for p in self.state["proposals"] if p["id"] == pid)
                    chosen_proposal["supporters"].append(agent["id"])
                    if chosen_proposal["creator_id"] != agent["id"]:
                        agent_by_id[chosen_proposal["creator_id"]]["influence"] += 1
                elif rid is not None:
                    chosen_religion = self.religion(rid)
                    if chosen_religion and chosen_religion["canonical_version_id"]:
                        creator_id = self.version(chosen_religion["canonical_version_id"])["creator_id"]
                        if creator_id is not None and creator_id != agent["id"]:
                            agent_by_id[creator_id]["influence"] += 1
                self.event("choose", f"{agent['name']} chose {self.religion(rid)['name'] if rid else 'no religion'}: {action.get('reason','')}",
                           agent_id=agent["id"], religion_id=rid, proposal_id=pid, previous_religion_id=old)
            else:
                self.create_proposal(agent, action, turn)

        self.resolve_proposals(turn)
        for r in self.state["religions"]:
            members = self.members(r["id"])
            supporters = current_support.get(r["id"], [])
            share = len(supporters) / len(members) if members else 0.0
            for a in members: a["life"] += share
        for a in self.state["agents"]:
            if not a["alive"]: continue
            a["life"] -= 1.0
            if a["life"] <= 0:
                a["alive"], a["died_turn"] = False, turn
                self.event("death", f"{a['name']} died after receiving insufficient support.", agent_id=a["id"], religion_id=a["religion_id"])
        for r in self.state["religions"]:
            if r["active"] and not self.members(r["id"]):
                r["active"] = False
                self.event("extinction", f"{r['name']} became extinct.", religion_id=r["id"])
        self.state["turn"] = turn
        self.state["usage"]["estimated_cost"] = round(self.state["usage"]["input_tokens"] * 0.30 / 1_000_000 + self.state["usage"]["output_tokens"] * 2.50 / 1_000_000, 4)
        if self.state["usage"]["estimated_cost"] >= self.args.cost_cap:
            self.state["finished"], self.state["finish_reason"] = True, "cost cap"
        elif not any(a["alive"] for a in self.state["agents"]):
            self.state["finished"], self.state["finish_reason"] = True, "all agents died"
        elif turn >= self.args.turns:
            self.state["finished"], self.state["finish_reason"] = True, "turn limit"

    def create_proposal(self, agent: dict, action: dict, turn: int) -> None:
        c, rid, parent = action["candidate"], action.get("religion_id"), action.get("parent_religion_id")
        is_foundation = rid is None
        if rid is None:
            rid = self.state["next_religion_id"]; self.state["next_religion_id"] += 1
            self.state["religions"].append({"id": rid, "name": c["name"], "canonical_version_id": None,
                                           "parent_religion_id": parent, "created_by": agent["id"], "created_turn": turn, "active": True})
            agent["religion_id"] = rid
        pid = self.state["next_proposal_id"]; self.state["next_proposal_id"] += 1
        art_path = self.out / "artworks" / f"proposal-{pid}.html"; art_path.write_text(c["artwork"])
        render_path = self.out / "renders" / f"proposal-{pid}.png"
        try: self.render_art(art_path, render_path)
        except Exception as exc:
            self.event("invalid_artwork", f"{agent['name']}'s artwork could not render: {exc}", agent_id=agent["id"]); return
        if is_foundation:
            vid = self.state["next_version_id"]; self.state["next_version_id"] += 1
            final_art = self.out / "artworks" / f"version-{vid}.html"
            final_render = self.out / "renders" / f"version-{vid}.png"
            final_art.write_text(art_path.read_text()); final_render.write_bytes(render_path.read_bytes())
            v = {"id": vid, "religion_id": rid, "parent_version_id": None, "creator_id": agent["id"],
                 "name": c["name"], "doctrine": c["doctrine"], "artwork_path": str(final_art.relative_to(self.out)),
                 "render_path": str(final_render.relative_to(self.out)), "reason": action.get("reason", ""),
                 "expected_effect": action.get("expected_effect", ""), "created_turn": turn, "resolved_turn": turn,
                 "status": "canonical", "supporters": []}
            self.state["versions"].append(v)
            r = self.religion(rid); r["canonical_version_id"] = vid; r["name"] = c["name"]
            append_jsonl(self.out / "versions.jsonl", v)
            self.event("founding", f"{agent['name']} founded {c['name']}: {action.get('reason','')}",
                       agent_id=agent["id"], religion_id=rid, version_id=vid, parent_religion_id=parent)
            return
        p = {"id": pid, "religion_id": rid, "creator_id": agent["id"], "creator_name": agent["name"],
             "candidate_name": c["name"], "candidate_doctrine": c["doctrine"],
             "artwork_path": str(art_path.relative_to(self.out)), "render_path": str(render_path.relative_to(self.out)),
             "reason": action.get("reason", ""), "expected_effect": action.get("expected_effect", ""),
             "created_turn": turn, "closes_after_turn": turn + self.args.proposal_lifetime, "status": "open", "supporters": []}
        self.state["proposals"].append(p); agent["active_proposal_id"] = pid
        self.event("proposal", f"{agent['name']} proposed {c['name']}: {p['reason']}", agent_id=agent["id"], religion_id=rid, proposal_id=pid)

    def resolve_proposals(self, turn: int) -> None:
        due_by_rel: dict[int, list[dict]] = {}
        for p in self.open_proposals():
            if turn >= p["closes_after_turn"]: due_by_rel.setdefault(p["religion_id"], []).append(p)
        for rid, proposals in due_by_rel.items():
            r = self.religion(rid)
            if not r: continue
            ranked = sorted(proposals, key=lambda p: len(p["supporters"]), reverse=True)
            winner = ranked[0] if ranked and len(ranked[0]["supporters"]) > 0 and (len(ranked) == 1 or len(ranked[0]["supporters"]) > len(ranked[1]["supporters"])) else None
            for p in proposals:
                creator = next(a for a in self.state["agents"] if a["id"] == p["creator_id"])
                creator["active_proposal_id"] = None
                p["status"] = "accepted" if p is winner else "rejected"
                if p is winner:
                    vid = self.state["next_version_id"]; self.state["next_version_id"] += 1
                    old_vid = r["canonical_version_id"]
                    final_art = self.out / "artworks" / f"version-{vid}.html"
                    final_render = self.out / "renders" / f"version-{vid}.png"
                    final_art.write_text((self.out / p["artwork_path"]).read_text()); final_render.write_bytes((self.out / p["render_path"]).read_bytes())
                    v = {"id": vid, "religion_id": rid, "parent_version_id": old_vid, "creator_id": p["creator_id"],
                         "name": p["candidate_name"], "doctrine": p["candidate_doctrine"],
                         "artwork_path": str(final_art.relative_to(self.out)), "render_path": str(final_render.relative_to(self.out)),
                         "reason": p["reason"], "expected_effect": p["expected_effect"], "created_turn": p["created_turn"],
                         "resolved_turn": turn, "status": "canonical", "supporters": p["supporters"]}
                    self.state["versions"].append(v); r["canonical_version_id"] = vid; r["name"] = v["name"]
                    append_jsonl(self.out / "versions.jsonl", v)
                    self.event("accepted", f"{v['name']} accepted version {vid} with {len(p['supporters'])} supporters.", religion_id=rid, proposal_id=p["id"], version_id=vid)
                else:
                    self.event("rejected", f"Proposal {p['id']} was rejected with {len(p['supporters'])} supporters.", religion_id=rid, proposal_id=p["id"])

    def event(self, kind: str, text: str, **fields: Any) -> None:
        e = {"turn": self.state["turn"] + 1, "time": utcnow(), "type": kind, "text": text, **fields}
        self.state["events"].append(e); append_jsonl(self.out / "events.jsonl", e)

    # ------------------------------------------------------------ pressure round
    # Conquest by conversion. Every --pressure-every turns, an EXTRA round runs in which
    # allegiance is re-decided from the canonical artworks alone: no names, no doctrines,
    # no members, no history, panels permuted per agent. It never replaces the turn's normal
    # make/choose action, so make-opportunities per turn are identical at every dial setting.
    # See docs/threat_dial_prereg.md in the cultural-selection-blog experiment.

    def pressure_panels(self, agent: dict, snapshot: dict) -> list[dict]:
        """Active religions in an order scrambled for this agent alone, reproducibly."""
        active = sorted([r for r in snapshot["religions"] if r["active"] and r["canonical_version_id"]],
                        key=lambda r: r["id"])
        order = list(range(len(active)))
        random.Random(f"{self.args.seed}:{snapshot['turn']}:{agent['id']}").shuffle(order)
        return [active[i] for i in order]

    def pressure_observation(self, panels: list[dict], snapshot: dict) -> tuple[str, list[Path]]:
        """Images only. Nothing here may identify a religion — that is the whole mechanic."""
        images = []
        for r in panels:
            v = next(x for x in snapshot["versions"] if x["id"] == r["canonical_version_id"])
            images.append(self.out / v["render_path"])
        payload = {"turn": snapshot["turn"], "panels": len(panels),
                   "image_order": [f"panel-{i + 1}.png" for i in range(len(panels))]}
        return json.dumps(payload, ensure_ascii=False, indent=2), images

    def scripted_ranking(self, agent: dict, panels: list[dict]) -> dict:
        n = len(panels)
        shift = agent["id"] % n if n else 0
        return {"ranking": [(i + shift) % n + 1 for i in range(n)], "reason": "Scripted ranking."}

    def gemini_ranking(self, panels: list[dict], snapshot: dict) -> dict:
        observation, images = self.pressure_observation(panels, snapshot)
        return self.gemini_json(self.system_prompt + "\n\n" + observation + "\n\n" + self.pressure_prompt, images)

    @staticmethod
    def validate_ranking(action: dict, n: int) -> tuple[bool, str]:
        ranking = action.get("ranking")
        if not isinstance(ranking, list): return False, "ranking must be a list"
        if len(ranking) != n: return False, f"ranking must cover all {n} panels"
        if sorted(ranking) != list(range(1, n + 1)): return False, "ranking must be a permutation of panel numbers"
        return True, "ok"

    def rank_one(self, agent: dict, snapshot: dict) -> dict:
        started = time.time()
        panels = self.pressure_panels(agent, snapshot)
        observation, images = self.pressure_observation(panels, snapshot)
        obs_record = {"turn": snapshot["turn"], "agent_id": agent["id"], "agent_name": agent["name"],
                      "observation_sha256": hashlib.sha256(observation.encode()).hexdigest(),
                      "observation": observation, "panel_religion_ids": [r["id"] for r in panels],
                      "images": [str(p.relative_to(self.out)) for p in images]}
        try:
            action = self.scripted_ranking(agent, panels) if self.args.dry_run else self.gemini_ranking(panels, snapshot)
            valid, error = self.validate_ranking(action, len(panels))
        except Exception as exc:
            action, valid, error = {"action": "invalid"}, False, f"{type(exc).__name__}: {exc}"
        return {"observation": obs_record, "panels": [r["id"] for r in panels],
                "decision": {"turn": snapshot["turn"], "agent_id": agent["id"], "agent_name": agent["name"],
                             "action": action, "valid": valid, "error": None if valid else error,
                             "latency_seconds": round(time.time() - started, 3)}}

    def apply_pressure(self, results: list[dict]) -> None:
        turn = self.state["turn"]
        agent_by_id = {a["id"]: a for a in self.state["agents"]}
        prefs: dict[int, list[int]] = {}
        for res in results:
            append_jsonl(self.out / "pressure_observations.jsonl", res["observation"])
            d = res["decision"]
            append_jsonl(self.out / "pressure_decisions.jsonl", d)
            usage = d["action"].get("_usage", {})
            self.state["usage"]["input_tokens"] += usage.get("input_tokens", 0)
            self.state["usage"]["output_tokens"] += usage.get("output_tokens", 0)
            self.state["usage"]["calls"] += 0 if self.args.dry_run else 1
            agent = agent_by_id[d["agent_id"]]
            if not d["valid"]:
                self.state["usage"]["errors"] += 1
                self.event("invalid_ranking", f"{d['agent_name']}'s ranking failed: {d['error']}", agent_id=agent["id"])
                # An agent who cannot rank keeps the allegiance it already had.
                prefs[agent["id"]] = [agent["religion_id"]] if agent["religion_id"] else []
                continue
            prefs[agent["id"]] = [res["panels"][p - 1] for p in d["action"]["ranking"]]

        for aid, pref in prefs.items():
            if not pref: continue
            agent, rid = agent_by_id[aid], pref[0]
            agent["religion_id"] = rid
            r = self.religion(rid)
            if r and r["canonical_version_id"]:
                creator_id = self.version(r["canonical_version_id"])["creator_id"]
                if creator_id is not None and creator_id != aid:
                    agent_by_id[creator_id]["influence"] += 1

        self.resolve_extinctions(prefs, agent_by_id, turn)
        counts = {r["name"]: len(self.members(r["id"])) for r in self.state["religions"] if r["active"]}
        self.event("pressure_round", f"Allegiance was tested on artwork alone: {json.dumps(counts, ensure_ascii=False)}")

    def resolve_extinctions(self, prefs: dict[int, list[int]], agent_by_id: dict[int, dict], turn: int) -> None:
        """Kill religions under --min-members, scatter their members down their own ranking.

        Iterative: a scatter can push another religion under the threshold. Religions younger
        than the grace period are exempt so that founding is not made impossible at high
        pressure -- a founder starts alone and needs turns to attract members.
        """
        grace = getattr(self.args, "min_members_grace", 0)
        while True:
            active = [r for r in self.state["religions"] if r["active"]]
            doomed = [r for r in active
                      if len(self.members(r["id"])) < self.args.min_members and turn - r["created_turn"] > grace]
            if not doomed: return
            if len(active) - len(doomed) < 1:
                self.event("pressure_stalemate",
                           "Every culture fell below the threshold at once; none was dissolved.")
                return
            doomed_ids = {r["id"] for r in doomed}
            for r in doomed:
                r["active"] = False
                self.event("extinction", f"{r['name']} lost its members when allegiance was tested.", religion_id=r["id"])
            survivors = {r["id"] for r in self.state["religions"] if r["active"]}
            for a in self.state["agents"]:
                if not a["alive"] or a["religion_id"] not in doomed_ids: continue
                fallback = next((rid for rid in prefs.get(a["id"], []) if rid in survivors), None)
                if fallback is None:
                    fallback = max(survivors, key=lambda rid: (len(self.members(rid)), -rid))
                a["religion_id"] = fallback
                self.event("scatter", f"{a['name']} fell to {self.religion(fallback)['name']}.",
                           agent_id=a["id"], religion_id=fallback)

    def pressure_round(self) -> None:
        snapshot = copy.deepcopy(self.state)
        alive = [a for a in snapshot["agents"] if a["alive"]]
        if not alive or len([r for r in snapshot["religions"] if r["active"] and r["canonical_version_id"]]) < 2:
            return
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.args.workers) as pool:
            results = list(pool.map(lambda a: self.rank_one(a, snapshot), alive))
        self.apply_pressure(results)

    def run_turn(self) -> None:
        snapshot = copy.deepcopy(self.state)
        alive = [a for a in snapshot["agents"] if a["alive"]]
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.args.workers) as pool:
            results = list(pool.map(lambda a: self.decide_one(a, snapshot), alive))
        self.apply_decisions(results)
        every = getattr(self.args, "pressure_every", 0)
        if every and self.state["turn"] % every == 0 and any(a["alive"] for a in self.state["agents"]):
            self.pressure_round()
        self.save()
        print(json.dumps({"turn": self.state["turn"], "alive": sum(a["alive"] for a in self.state["agents"]),
                          "religions": sum(r["active"] for r in self.state["religions"]),
                          "open_proposals": len(self.open_proposals()),
                          "top_influence": max((a.get("influence", 0) for a in self.state["agents"]), default=0),
                          "usage": self.state["usage"]}), flush=True)

    def generate_site(self, state: dict) -> None:
        cards = []
        for r in state["religions"]:
            if not r["active"] or not r["canonical_version_id"]: continue
            v = next(x for x in state["versions"] if x["id"] == r["canonical_version_id"])
            member_names = ", ".join(a["name"] for a in state["agents"] if a["alive"] and a["religion_id"] == r["id"])
            src = "../" + v["artwork_path"]
            cards.append(f'<article><iframe sandbox src="{html.escape(src)}"></iframe><h2>{html.escape(v["name"])}</h2><p>{html.escape(v["doctrine"])}</p><small>{html.escape(member_names)}</small></article>')
        events = "".join(f"<li><b>{e['type']}</b> {html.escape(e['text'])}</li>" for e in state["events"][-30:][::-1])
        page = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Minimal Cultural Selection</title><style>
body{{margin:0;background:#08090e;color:#e8e6df;font:16px/1.5 system-ui}}header,main{{max-width:1200px;margin:auto;padding:28px}}header{{display:flex;justify-content:space-between;align-items:end}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}}article{{background:#11131c;border:1px solid #292c3b;padding:14px}}iframe{{width:100%;aspect-ratio:1;border:0;background:#000}}h1{{font:42px Georgia}}h2{{font:24px Georgia;margin-bottom:4px}}p,small,li{{color:#aaaabd}}.stats{{color:#d5bf55}}li{{margin:.5em 0}}
</style></head><body><header><div><small>RELIGION &amp; THE MACHINE</small><h1>Minimal Cultural Selection</h1></div><div class="stats">Turn {state['turn']} · {sum(a['alive'] for a in state['agents'])} alive · ${state['usage']['estimated_cost']:.2f}</div></header><main><section class="grid">{''.join(cards)}</section><h1>Public history</h1><ol>{events}</ol></main></body></html>'''
        (self.out / "site" / "index.html").write_text(page)

    def run(self) -> None:
        config = vars(self.args).copy(); config["started_at"] = utcnow(); json_dump(self.out / "config.json", config)
        while not self.state["finished"] and self.state["turn"] < self.args.turns:
            self.run_turn()
            u = self.state["usage"]
            if self.state["turn"] >= 3 and u["calls"] > 0 and u["errors"] == u["calls"]:
                self.state["finished"] = True
                self.state["finish_reason"] = "aborted: every API call errored (check keys/quota)"
        (self.out / "COMPLETE").write_text(f"{utcnow()} {self.state['finish_reason']}\n")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--run-dir", default=str(ROOT / "outputs/2026-07-12-minimal-cultural-selection"))
    p.add_argument("--model", default="gemini-2.5-flash")
    p.add_argument("--agents", type=int, default=24); p.add_argument("--turns", type=int, default=100)
    p.add_argument("--initial-life", type=int, default=20); p.add_argument("--proposal-lifetime", type=int, default=3)
    p.add_argument("--workers", type=int, default=8); p.add_argument("--seed", type=int, default=46)
    p.add_argument("--cost-cap", type=float, default=100.0); p.add_argument("--dry-run", action="store_true")
    p.add_argument("--fresh", action="store_true")
    p.add_argument("--charter-file", default=None,
                   help="Path to a founding-charter markdown file injected into the system prompt")
    p.add_argument("--seed-art-dir", default=None,
                   help="Directory holding seed-1..4.html, the founding artwork of each seed religion "
                        "(default: the built-in generated template)")
    p.add_argument("--no-words", action="store_true",
                   help="Artworks may contain no letters or numerals: adds the rule to the system prompt "
                        "and enforces it in validate_art")
    p.add_argument("--pressure-every", type=int, default=0,
                   help="Run an art-only allegiance round every K turns (0 = never, the control)")
    p.add_argument("--min-members", type=int, default=3,
                   help="Religions below this many members are dissolved by a pressure round")
    p.add_argument("--min-members-grace", type=int, default=0,
                   help="Religions younger than this many turns are exempt from --min-members")
    p.add_argument("--announce-pressure", action="store_true",
                   help="Tell agents allegiance is periodically tested (set for ALL threat-dial worlds, control included)")
    return p


if __name__ == "__main__":
    Game(parser().parse_args()).run()
