"""Base stats per tier and form: what the profiles' gear showed, on top of the committed table src/observed.json.

{tier: {slot kind: {form: [attack, defense, support]}}}, with the points of stones and upgrades taken out.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SEED = Path(__file__).with_name("observed.json")
FOCUS = {"ATTACK": 0, "DEFENSE": 1, "SUPPORT": 2}
GEM = {"Angriff": 0, "Verteidigung": 1, "Unterstützung": 2}
UPGRADE_POINTS = {"w1": {0, 1, 3, 4, 6}, "armor": {0, 1, 3, 4, 6}, "shield": {0, 1, 3, 4, 6},
                  "w2": {0, 3, 5, 8, 11}, "ring": {0, 1, 2, 3, 4}}
FORM = re.compile(r" ((?:des|der) .+)$")


def kind_of(slot: str, name: str, two_handed: bool) -> str:
    if slot in ("RING", "RING_2"):
        return "ring"
    if slot == "WEAPON":
        return "w2" if two_handed else "w1"
    if slot == "SHIELD":
        return "w1" if FORM.search(name) and not name.startswith("Ägis") else "shield"
    return "armor"


def total(kind: str, tier: int) -> int:
    return 3 * tier if kind == "ring" else (2 if kind == "w2" else 1) * (5 * tier + 3)


def base_of(slot: str, v: list) -> tuple[str, str, str, list[int]] | None:
    """(tier, kind, form, base stats) of a profile slot entry (see collect.watch_entry), or None when the stat
    split can't be backed out cleanly (boss loot, a name without a form, points that fit no upgrade)."""
    if len(v) < 13 or not v[1] or v[12]:
        return None
    name, tier, base, socket, level, focus = v[1], v[2], [v[3], v[4], v[5]], v[8] or "", v[10], v[11]
    kind = kind_of(slot, name, bool(v[9]))
    gem = re.match(r"(Angriff|Verteidigung|Unterstützung) \+(\d+)", socket)
    gem_points = int(gem[2]) if gem else 0
    points = sum(base) - total(kind, tier) - gem_points
    if points not in UPGRADE_POINTS[kind] or bool(points) != bool(level):
        return None
    if gem:
        base[GEM[gem[1]]] -= gem_points
    if points:
        if focus not in FOCUS:
            return None
        base[FOCUS[focus]] -= points
    clean = re.sub(r" \+\d+$", "", name)
    form = clean.split()[-1] if kind == "shield" else (m[1] if (m := FORM.search(clean)) else None)
    if min(base) < 0 or form is None or sum(base) != total(kind, tier):
        return None
    return str(tier), kind, form, base


def observed(state: dict) -> dict:
    """The committed table plus every clean piece the profiles in `state` show."""
    table = json.loads(SEED.read_text("utf-8"))
    for entry in (state.get("watch") or {}).values():
        for slot, v in (entry.get("slots") or {}).items():
            if piece := base_of(slot, v):
                tier, kind, form, base = piece
                table.setdefault(tier, {}).setdefault(kind, {})[form] = base
    return table
