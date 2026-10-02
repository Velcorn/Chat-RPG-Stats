"""Collector: one snapshot of the game's public data, stored as the changes since the last one.

Runs every 15 minutes in GitHub Actions during the game's play window. Reads only public endpoints (no login,
no cookies) and never sends anything but GETs. One run is about fifteen requests plus one per new fight, two
seconds apart.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

BASE = "https://rpg.sola.rip"
BERLIN = ZoneInfo("Europe/Berlin")
PLAY_FROM, PLAY_TO = 7, 24  # the game's play window (Berlin time); nothing changes outside it
PAUSE = 2.0
# The site's four rankings (`by=` value -> the value they rank by). Others (silver, level) just return the gear board.
BOARD_FIELDS = {"gear": "gearScore", "gold": "silver", "errungenschaften": "achievements", "quests": "quests"}


def user_agent() -> str:
    repo = os.getenv("GITHUB_REPOSITORY", "Velcorn/Chat-RPG-Stats")
    return f"Chat-RPG-Stats (read-only community stats, https://github.com/{repo})"


class Site:
    def __init__(self, pause: float = PAUSE):
        self.pause, self.requests = pause, 0

    def get(self, path: str):
        if self.requests:
            time.sleep(self.pause)
        self.requests += 1
        req = urllib.request.Request(BASE + path, headers={"User-Agent": user_agent(), "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)


def read_watchlist(path: Path) -> list[str]:
    if not path.exists():
        return []
    names = (line.split("#")[0].strip().lower() for line in path.read_text("utf-8").splitlines())
    return sorted({n for n in names if n})


def snapshot(site: Site, watchlist: list[str], detail_after: int = 0) -> dict:
    """Everything one run asks the site, in the site's own shapes. Fights newer than `detail_after` also cost one
    request for their detail page (the archive's own numbers: who fell, roles, damage)."""
    snap: dict = {"guilds": {}, "watch": {}, "details": {}}
    for g in site.get("/api/guilds"):
        if g.get("members"):
            snap["guilds"][g["login"]] = site.get(f"/api/guilds/{quote(g['login'])}")
    snap["boards"] = {b: site.get(f"/api/leaderboard?by={b}&limit=100") for b in BOARD_FIELDS}
    snap["fights"] = site.get("/api/combat/history")
    for f in sorted(snap["fights"], key=lambda f: f.get("id", 0)):
        if f.get("id", 0) > detail_after:
            try:
                snap["details"][f["id"]] = site.get(f"/api/combat/history/{f['id']}")
            except urllib.error.HTTPError as exc:
                exc.close()
                if exc.code != 404:
                    raise
    snap["live"] = site.get("/api/combat?kompakt=true")
    snap["channels"] = site.get("/api/channels")
    for login in watchlist:
        try:
            snap["watch"][login] = site.get(f"/api/players/{quote(login)}")
        except urllib.error.HTTPError as exc:
            exc.close()
            if exc.code != 404:
                raise
    return snap


ROLES = ("TANK", "FIGHTER", "SUPPORT")


def silver_value(text: str | None) -> int | None:
    """"+4 Gold 65 Silber" -> 465, "-3 Gold 36 Silber" (with the game's minus sign) -> -336."""
    m = re.fullmatch(r"([+\u2212-])\s*(?:(\d+) Gold)?\s*(?:(\d+) Silber)?", (text or "").strip())
    if not m or not (m[2] or m[3]):
        return None
    value = int(m[2] or 0) * 100 + int(m[3] or 0)
    return -value if m[1] != "+" else value


def detail_digest(d: dict) -> dict:
    """What one finished fight's detail page adds up to: sums and counts only, nothing per player."""
    n, dead, pay = [0, 0, 0], [0, 0, 0], {True: [], False: []}
    for f in d.get("fighters") or []:
        if f.get("role") in ROLES:
            i = ROLES.index(f["role"])
            n[i] += 1
            dead[i] += not f.get("alive")
        if (v := silver_value(f.get("gold"))) is not None:
            pay[bool(f.get("alive"))].append(v)
    tally = (d.get("crowd") or {}).get("tally") or {}
    mean = lambda xs: round(sum(xs) / len(xs)) if xs else None  # noqa: E731
    return {"roles": n, "dead": dead, "dmg": tally.get("damage"), "taken": tally.get("taken"),
            "heal": tally.get("healing"), "boost": tally.get("boosted"), "round": d.get("round"),
            "rounds": d.get("maxRounds"), "hp": d.get("hp"), "maxhp": d.get("maxHp"),
            "pay": [mean(pay[True]), mean(pay[False])]}


def live_digest(e: dict) -> dict:
    """The live view of a just finished fight has what the archive lacks: average gear and power, the
    recommendation and the fight engine's numbers. Only the fight the site still shows."""
    b = e.get("battle") or {}
    return {"gear": e.get("averageGear"), "power": e.get("averagePower"), "rec": e.get("recommendedGear"),
            "min": e.get("minGear"), "verdict": e.get("verdict"), "secs": b.get("secondsFought"),
            "enraged": b.get("enraged"), "gs": b.get("groupStrength"), "gsmax": b.get("groupStrengthMax"),
            "tanks": [b.get("tanksStanding"), b.get("tanksTotal")]}


def state_from(snap: dict, prev: dict) -> dict:
    """The flat current state: compact values per player, guild, board and channel."""
    players: dict[str, dict] = {}
    guilds: dict[str, dict] = {}
    for glogin, page in snap["guilds"].items():
        g, boss = page.get("guild") or {}, page.get("boss") or {}
        guilds[glogin] = {"name": g.get("name"), "treasury": g.get("treasurySilver"), "members": g.get("members"),
                          "active": g.get("activeMembers"), "gear": g.get("gearScore"), "raid": g.get("raidLevel"),
                          "boss_wins": boss.get("wins"), "boss_losses": boss.get("losses")}
        for m in page.get("members") or []:
            players[m["login"].lower()] = {"name": m.get("displayName"), "gear": m.get("gearScore"),
                                           "donated": m.get("donatedSilver"), "active": m.get("active"),
                                           "guild": glogin, "joined": m.get("joinedAt")}
    details: dict[str, dict] = {}
    # The board lags a few minutes behind the guild pages; its own value is kept, so its order makes sense.
    boards: dict[str, list] = {}
    for board, rows in snap["boards"].items():
        boards[board] = [[r["login"].lower(), r.get(BOARD_FIELDS[board])] for r in rows]
        for r in rows:
            login = r["login"].lower()
            details[login] = {"atk": r.get("attack"), "def": r.get("defense"), "sup": r.get("support"),
                              "silver": r.get("silver"), "quests": r.get("quests"), "ach": r.get("achievements")}
            if login not in players:  # on the board but in no guild
                players[login] = {"name": r.get("displayName"), "gear": r.get("gearScore"), "donated": None,
                                  "active": None, "guild": None}
    watch: dict[str, dict] = {}
    for login, p in snap["watch"].items():
        slots = {s["slot"]: [s.get("label"), i.get("name"), i.get("tier"), i.get("attack"), i.get("defense"),
                             i.get("support"), bool(i.get("damaged"))] if (i := s.get("item")) else [s.get("label")]
                 for s in p.get("slots") or []}
        watch[login] = {"survival": p.get("survivalPercent"), "life": p.get("life"),
                        "ach": p.get("achievementsUnlocked"), "stats": p.get("stats") or {}, "slots": slots}
        details[login] = {**details.get(login, {}), "atk": p.get("attack"), "def": p.get("defense"),
                          "sup": p.get("support"), "silver": p.get("silver")}
        if login not in players:
            players[login] = {**prev.get("players", {}).get(login, {}), "name": p.get("displayName"),
                              "guild": (p.get("guild") or {}).get("login")}
    # Seen before but in no guild and on no board now: left their guild. The last gear score stays known.
    for login, old in prev.get("players", {}).items():
        if login not in players:
            players[login] = {**old, "guild": None, "active": None}
    return {"players": players, "details": {**prev.get("details", {}), **details}, "boards": boards,
            "guilds": guilds, "watch": watch,
            "channels": {c["login"]: bool(c.get("live")) for c in snap["channels"] if c.get("enabled")},
            "fight_last": max([prev.get("fight_last", 0), *(f.get("id", 0) for f in snap["fights"])]),
            "detail_last": max([prev.get("detail_last", 0), *snap.get("details", {})]),
            "live_seen": sorted({*prev.get("live_seen", []), *live_ids(snap)})[-30:]}


def live_ids(snap: dict) -> list[int]:
    return [e["archiveId"] for e in snap.get("live") or [] if e.get("archiveId") and e.get("phase") != "SIGNUP"
            and e.get("endedAt")]


def changed(old: dict, new: dict) -> dict:
    """Entries of `new` that are new or differ from `old`; of an entry seen before, only the fields that changed."""
    out = {}
    for k, v in new.items():
        before = old.get(k)
        if before == v:
            continue
        if isinstance(v, dict) and isinstance(before, dict):
            v = {f: x for f, x in v.items() if before.get(f) != x}
        out[k] = v
    return out


def record(snap: dict, prev: dict, cur: dict, t: int) -> dict:
    """One line of history: only what changed since `prev`, plus new fights."""
    rec: dict = {"t": t}
    for key in ("players", "details", "guilds", "channels", "watch"):
        if diff := changed(prev.get(key, {}), cur[key]):
            rec[key] = diff
    if boards := changed(prev.get("boards", {}), cur["boards"]):
        rec["boards"] = boards
    last = prev.get("fight_last", 0)
    fights = [{k: f.get(k) for k in ("id", "channel", "kind", "name", "difficulty", "bossLevel", "outcome",
                                      "fighters", "endedAt")} for f in snap["fights"] if f.get("id", 0) > last]
    if fights:
        rec["fights"] = sorted(fights, key=lambda f: f["id"])
    extra: dict[int, dict] = {i: detail_digest(d) for i, d in snap.get("details", {}).items()}
    seen = set(prev.get("live_seen", []))
    for e in snap.get("live") or []:
        if e.get("archiveId") in live_ids(snap) and e["archiveId"] not in seen:
            extra[e["archiveId"]] = {**extra.get(e["archiveId"], {}), **live_digest(e)}
    if extra:
        rec["fightx"] = extra
    return rec


def in_play_window(now: datetime) -> bool:
    return PLAY_FROM <= now.hour < PLAY_TO


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--watchlist", type=Path, default=Path("watchlist.txt"))
    ap.add_argument("--force", action="store_true", help="also outside the play window")
    args = ap.parse_args()
    now = datetime.now(BERLIN)
    if not args.force and not in_play_window(now):
        print("Außerhalb der Spielzeit, nichts zu tun.")
        return 0
    site = Site()
    state_file = args.data / "state.json"
    prev = json.loads(state_file.read_text("utf-8")) if state_file.exists() else {}
    try:
        snap = snapshot(site, read_watchlist(args.watchlist), prev.get("detail_last", 0))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        # The site is down or busy: skip this run instead of failing (and retrying) on every schedule.
        print(f"Seite nicht erreichbar, Lauf übersprungen: {exc}")
        return 0
    cur = state_from(snap, prev)
    rec = record(snap, prev, cur, int(now.timestamp()))
    rec["req"] = site.requests  # the site shows the load it puts on the game
    days = args.data / "days"
    days.mkdir(parents=True, exist_ok=True)
    with (days / f"{now:%Y-%m-%d}.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    tmp = state_file.with_name("state.json.tmp")
    tmp.write_text(json.dumps(cur, ensure_ascii=False, separators=(",", ":")), "utf-8")
    os.replace(tmp, state_file)
    if out := os.getenv("GITHUB_OUTPUT"):
        with open(out, "a", encoding="utf-8") as fh:
            fh.write("collected=true\n")
    print(f"{site.requests} Anfragen, {len(rec) - 1} geänderte Bereiche, "
          f"{len(rec.get('players', {}))} Spieler mit Änderungen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
