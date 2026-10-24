"""Collector: one snapshot of the game's public data, stored as the changes since the last one.

Runs every 15 minutes in GitHub Actions during the game's play window. Reads only public endpoints (no login,
no cookies) and never sends anything but GETs. One run is about seventeen requests plus one per new fight and a
slice of the active players' profiles (about 55, so every active player is read about once a day), two seconds
apart; once a day come the first kills (one).
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
PAUSE = 2.0
BOUND_SOURCES = ("PERSONAL_SHOP", "AUCTION", "TRADER", "SEALED")  # bound to the player, not for the market
RUNS_PER_DAY = 224  # a run every 5 minutes, round the clock, but every 15 from 1 to 9 o'clock (16 * 12 + 8 * 4)
SWEEP_RUNS = 180  # the active players' profiles are read in this many slices: each one about once a day (60 at 15 min)
TOP_WATCH = 100  # the board's top players get the watchlist's detailed profile data, all in the day's first run
# The site's four rankings (`by=` value -> the value they rank by). Others (silver, level) just return the gear board.
BOARD_FIELDS = {"gear": "gearScore"}


def user_agent() -> str:
    repo = os.getenv("GITHUB_REPOSITORY", "Velcorn/Chat-RPG-Stats")
    return f"Chat-RPG-Stats (read-only community stats, https://github.com/{repo})"


class Site:
    def __init__(self, pause: float = PAUSE):
        self.pause, self.requests = pause, 0

    def fetch(self, path: str, accept: str) -> bytes:
        if self.requests:
            time.sleep(self.pause)
        self.requests += 1
        req = urllib.request.Request(BASE + path, headers={"User-Agent": user_agent(), "Accept": accept})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()

    def get(self, path: str):
        return json.loads(self.fetch(path, "application/json"))


# From this line on watchlist.txt lists the board's top 100, kept in sync by `watchlist.sync`. Those are read the
# way the top 100 always were (once a day and when their gear changed), not in every run like the entries above it.
AUTO_MARK = "# --- Top 100 (automatisch, bitte hier nichts eintragen) ---"


def manual_lines(text: str) -> tuple[list[str], list[str] | None]:
    """The lines above the automatic part, and the automatic part's lines (None: the file has none yet)."""
    lines = text.splitlines()
    cut = next((i for i, line in enumerate(lines) if line.strip() == AUTO_MARK), None)
    return (lines, None) if cut is None else (lines[:cut], lines[cut + 1:])


def read_watchlist(path: Path) -> list[str]:
    """The entries read in every run: the channel owners and the ones added by hand, not the top 100 part."""
    if not path.exists():
        return []
    names = (line.split("#")[0].strip().lower() for line in manual_lines(path.read_text("utf-8"))[0])
    return sorted({n for n in names if n})


# Reference data read once a day (on the first run of a day that has not got it): name -> how to read it.
DAILY = {"first_kills": lambda site: site.get("/api/guilds/first-kills"),
         "compendium": lambda site: site.get("/api/compendium")}


def sweep_batch(logins: list[str], after: str, runs: int = SWEEP_RUNS) -> list[str]:
    """The next slice of `logins` (sorted) after the login the last run ended with; wraps around at the end."""
    ordered = sorted(set(logins))
    size = -(-len(ordered) // runs)
    rest = [x for x in ordered if x > after]
    return (rest + [x for x in ordered if x <= after])[:size]


def snapshot(site: Site, watchlist: list[str], detail_after: int = 0, daily: dict[str, str] | None = None,
             sweep_after: str = "", top_day: str = "", part: str = "all", prev: dict | None = None) -> dict:
    """Everything one run asks the site, in the site's own shapes. Fights newer than `detail_after` also cost one
    request for their detail page (the archive's own numbers: who fell, roles, damage). `daily` maps the reference
    data that is due (the guilds' first kills; they hardly ever change) to
    today's date; what was read lands in the snapshot with its date in `days`. The board (top 100) and the watchlist
    give the plain gear score anyway; of the other active guild members a slice (after the login `sweep_after`) gets
    its profile read, since only the profile (attack + defense + support) has it. The detail data of the watchlist
    (gear per slot, stats) is also read for the board's top 100, all at once on the first run of a day
    (`top_day` is today's date then), so every one of them is as old as the same morning.
    `part` splits a run in two so the page can be published after the quick first one: "core" asks everything but the
    profiles, "profiles" only the profiles (who is due comes from the last state `prev`), "all" is both."""
    snap: dict = {"guilds": {}, "watch": {}, "details": {}, "sweep": {},
                  "listed": list(watchlist)}
    if part == "profiles":
        snap |= {"fights": [], "boards": {}}
        return read_profiles(site, snap, watchlist, sweep_after, top_day, prev or {})
    for g in site.get("/api/guilds"):
        if g.get("members") or g.get("treasurySilver"):  # an empty guild with a treasury still fights bosses
            login = g["login"]
            snap["guilds"][login] = site.get(f"/api/guilds/{quote(login)}")
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
    snap["rules"] = site.get("/api/rules")
    for name, day in (daily or {}).items():
        try:
            snap[name] = DAILY[name](site)
            snap.setdefault("days", {})[name] = day
        except urllib.error.HTTPError as exc:  # an extra: a failing page must not cost the rest of the run
            exc.close()
        except (urllib.error.URLError, TimeoutError, ValueError, IndexError):
            pass
    snap["top"] = [r["login"].lower() for r in snap["boards"]["gear"][:TOP_WATCH]]
    return snap if part == "core" else read_profiles(site, snap, watchlist, sweep_after, top_day, prev or {})


def slot_sum(entry: dict | None) -> int | None:
    """The gear score a kept profile had: attack + defense + support of its worn pieces (None without one)."""
    if not entry or not entry.get("slots"):
        return None
    return sum(sum(v[i] or 0 for i in (3, 4, 5)) for v in entry["slots"].values() if len(v) > 5)


def read_profiles(site: Site, snap: dict, watchlist: list[str], sweep_after: str, top_day: str, prev: dict) -> dict:
    """The profile reads of a run: the watchlist, the board's top 100 (all once a day, and in every run those whose
    gear score on the board moved away from their last profile) and a slice of the other active guild members. In a
    full run the board and the guilds are in `snap`; in a profiles-only part they come from the last state `prev`."""
    for login in watchlist:
        try:
            snap["watch"][login] = site.get(f"/api/players/{quote(login)}")
        except urllib.error.HTTPError as exc:
            exc.close()
            if exc.code != 404:
                raise
    if snap["boards"]:
        board = [r["login"].lower() for r in snap["boards"]["gear"]]
        scores = {r["login"].lower(): r.get("gearScore") for r in snap["boards"]["gear"]}
        members = [m["login"].lower() for page in snap["guilds"].values() for m in page.get("members") or []
                   if m.get("active")]
    else:
        board = [login for login, _ in prev.get("boards", {}).get("gear", [])]
        scores = dict(prev.get("boards", {}).get("gear", []))
        members = [login for login, p in prev.get("players", {}).items() if p.get("active")]
    top = snap["top"] = board[:TOP_WATCH]
    # Between the morning reads only those whose gear changed: the board's score against the sum of the gear of the
    # last profile (about 6 of 100 a run, measured 09.-11.10.2026).
    kept = prev.get("watch", {})
    due_top = [x for x in top if x not in watchlist and (top_day or slot_sum(kept.get(x)) != scores.get(x))]
    for login in due_top:
        try:  # an extra: a failing page must not cost the rest of the run
            snap["watch"][login] = site.get(f"/api/players/{quote(login)}")
        except urllib.error.HTTPError as exc:
            exc.close()
            if exc.code != 404:
                break
        except (urllib.error.URLError, TimeoutError, ValueError):
            break
    else:
        if top_day:
            snap.setdefault("days", {})["top"] = top_day
    known = set(board) | set(watchlist)
    due = sweep_batch([login for login in members if login not in known], sweep_after)
    for login in due:  # an extra: a failing page must not cost the rest of the run
        try:
            snap["sweep"][login] = site.get(f"/api/players/{quote(login)}")
        except urllib.error.HTTPError as exc:
            exc.close()
            if exc.code != 404:
                break
        except (urllib.error.URLError, TimeoutError, ValueError):
            break
        snap["sweep_after"] = login
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
    by_role = [[0, 0, 0, 0] for _ in ROLES]  # per role: damage, taken, healing, boosted
    for f in d.get("fighters") or []:
        if f.get("role") in ROLES:
            i = ROLES.index(f["role"])
            n[i] += 1
            dead[i] += not f.get("alive")
            for j, key in enumerate(("damage", "damageTaken", "healing", "boosted")):
                by_role[i][j] += f.get(key) or 0
        if (v := silver_value(f.get("gold"))) is not None:
            pay[bool(f.get("alive"))].append(v)
    tally = (d.get("crowd") or {}).get("tally") or {}
    mean = lambda xs: round(sum(xs) / len(xs)) if xs else None  # noqa: E731
    # Whose fight it was: the guild it is about (a raid on its treasury, a boss it summoned), the summoner's channel
    # and what the treasury lost or won (the game's text, parsed). Only what the page has.
    guild = {k: v for k, v in (("gn", d.get("guildName")), ("by", d.get("summonedBy")),
                               ("gc", silver_value(d.get("treasuryChange"))),
                               ("go", True if d.get("guildOnly") else None)) if v is not None}
    return {**guild, "roles": n, "dead": dead, "rsum": by_role,
            "dmg": tally.get("damage"), "taken": tally.get("taken"), "heal": tally.get("healing"),
            "boost": tally.get("boosted"),
            "round": d.get("round"), "rounds": d.get("maxRounds"), "hp": d.get("hp"), "maxhp": d.get("maxHp"),
            "pay": [mean(pay[True]), mean(pay[False])]}


def live_digest(e: dict) -> dict:
    """The live view of a just finished fight has what the archive lacks: average gear and power, the
    recommendation and the fight engine's numbers. Only the fight the site still shows."""
    b = e.get("battle") or {}
    return {"gear": e.get("averageGear"), "power": e.get("averagePower"), "rec": e.get("recommendedGear"),
            "gg": e.get("groupGear") or None, "ggf": bool(e.get("groupGearFinal")),
            "min": e.get("minGear"), "verdict": e.get("verdict"), "secs": b.get("secondsFought"),
            "enraged": b.get("enraged"), "gs": b.get("groupStrength"), "gsmax": b.get("groupStrengthMax"),
            "tanks": [b.get("tanksStanding"), b.get("tanksTotal")]}


def boss_rec_state(page) -> dict[str, int]:
    """The recommended gear of every boss now, by name (the compendium; a boss without one is left out). The fights
    of a boss before its recommendation changed (it was made stronger) are not comparable to today's."""
    bosses = page.get("bosses") if isinstance(page, dict) else None
    return {b["name"]: int(b["recommendedGear"]) for b in bosses or []
            if isinstance(b, dict) and b.get("name") and b.get("recommendedGear")}


def first_kills_state(rows) -> list[list]:
    """The guilds' first kills as [boss, level, guild login, guild name, time, boss order], in the game's order."""
    return [[r.get("bossName"), r.get("level"), r.get("guildLogin"), r.get("guildName"), r.get("at"),
             r.get("bossOrder")] for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def guild_state(page: dict) -> dict:
    g, boss = page.get("guild") or {}, page.get("boss") or {}
    return {"name": g.get("name"), "treasury": g.get("treasurySilver"), "members": g.get("members"),
            "active": g.get("activeMembers"), "gear": g.get("gearScore"), "raid": g.get("raidLevel"),
            "boss_wins": boss.get("wins"), "boss_losses": boss.get("losses"), "boss_gear": boss.get("averageGear")}


def state_from(snap: dict, prev: dict) -> dict:
    """The flat current state: compact values per player, guild, board and channel."""
    players: dict[str, dict] = {}
    guilds: dict[str, dict] = {}
    for glogin, page in snap["guilds"].items():
        guilds[glogin] = guild_state(page)
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
    for login, p in snap.get("sweep", {}).items():
        details[login] = {**prev.get("details", {}).get(login, {}), "atk": p.get("attack"), "def": p.get("defense"),
                          "sup": p.get("support"), "silver": p.get("silver")}
    # Watchlist and top 100: what was read this run, else what was kept from the last state: the top 100's and the
    # watchlist's (a core part reads no profile; the profiles part after it reads them again).
    keep = {*snap.get("top", ()), *snap.get("listed", ())}
    watch: dict[str, dict] = {login: w for login, w in prev.get("watch", {}).items() if login in keep}
    for login, p in snap["watch"].items():
        watch[login] = watch_entry(p)
        details[login] = {**details.get(login, {}), "atk": p.get("attack"), "def": p.get("defense"),
                          "sup": p.get("support"), "silver": p.get("silver")}
        if login not in players:
            players[login] = {**prev.get("players", {}).get(login, {}), "name": p.get("displayName"),
                              "guild": (p.get("guild") or {}).get("login")}
    # The plain gear score (attack + defense + support): the profiles give it, the board its own value for the
    # top 100 (so its order makes sense); a player not read this run keeps the last one.
    scores = profile_scores(snap)
    scores.update({r["login"].lower(): r["gearScore"] for r in snap["boards"].get("gear", [])
                   if r.get("gearScore") is not None})
    for login, p in players.items():
        if (gs := scores.get(login, prev.get("players", {}).get(login, {}).get("gs"))) is not None:
            p["gs"] = gs
    # The board's attack, defense and support leave out upgrades and stones (its gear score has them; checked
    # 11.10.2026). The profile's gear per slot has everything: while its sum still matches the gear score, its split
    # replaces the board's.
    for login, w in watch.items():
        if login in snap["watch"] or not w.get("slots"):
            continue
        split = [sum(v[i] or 0 for v in w["slots"].values() if len(v) > i) for i in (3, 4, 5)]
        if sum(split) == players.get(login, {}).get("gs"):
            details[login] = {**details.get(login, {}), "atk": split[0], "def": split[1], "sup": split[2]}
    # Seen before but in no guild and on no board now: left their guild. The last gear score stays known.
    for login, old in prev.get("players", {}).items():
        if login not in players:
            players[login] = {**old, "guild": None, "active": None}
    return {"players": players, "details": {**prev.get("details", {}), **details}, "boards": boards,
            "guilds": guilds, "watch": watch,
            "channels": {c["login"]: bool(c.get("live")) for c in snap["channels"] if c.get("enabled")},
            "rules": {k: v for k, v in (snap.get("rules") or {}).items() if k != "playWindowOpenNow"},
            "first_kills": (first_kills_state(snap["first_kills"]) if "first_kills" in snap
                            else prev.get("first_kills", [])),
            "boss_rec": (boss_rec_state(snap["compendium"]) if "compendium" in snap else prev.get("boss_rec", {})),
            "days": {**prev.get("days", {}), **snap.get("days", {})},
            "fight_last": max([prev.get("fight_last", 0), *(f.get("id", 0) for f in snap["fights"])]),
            "sweep_after": snap.get("sweep_after", prev.get("sweep_after", "")),
            "detail_last": max([prev.get("detail_last", 0), *snap.get("details", {})]),
            "live_seen": sorted({*prev.get("live_seen", []), *live_ids(snap)})[-30:]}


def watch_entry(p: dict) -> dict:
    """What is kept of a detailed profile: survival, life, achievements, stat totals and the gear per slot."""
    slots = {s["slot"]: [s.get("label"), i.get("name"), i.get("tier"), i.get("attack"), i.get("defense"),
                         i.get("support"), i.get("durability"), int(i.get("source") in BOUND_SOURCES),
                         i.get("socket"), int(bool(i.get("twoHanded"))), i.get("upgrade") or 0, i.get("upgradeFocus"),
                         int(bool(i.get("bossLoot")))]
             if (i := s.get("item")) else [s.get("label")]
             for s in p.get("slots") or []}
    return {"survival": p.get("survivalPercent"), "life": p.get("life"), "ach": p.get("achievementsUnlocked"),
            "stats": p.get("stats") or {}, "slots": slots}


def profile_scores(snap: dict) -> dict[str, int]:
    """The plain gear score (attack + defense + support) of the profiles read this run."""
    return {login: p["attack"] + p["defense"] + p["support"]
            for login, p in {**snap.get("sweep", {}), **snap["watch"]}.items()
            if all(p.get(k) is not None for k in ("attack", "defense", "support"))}


def profiles_state(snap: dict, prev: dict) -> dict:
    """The state after a profiles-only part: the last state with the profiles read now merged in, as `state_from` does
    with them in a full run (a player on the gear board keeps the board's own score)."""
    players = {login: dict(p) for login, p in prev.get("players", {}).items()}
    details, watch = dict(prev.get("details", {})), dict(prev.get("watch", {}))
    for login, p in {**snap.get("sweep", {}), **snap["watch"]}.items():
        details[login] = {**details.get(login, {}), "atk": p.get("attack"), "def": p.get("defense"),
                          "sup": p.get("support"), "silver": p.get("silver")}
    for login, p in snap["watch"].items():
        watch[login] = watch_entry(p)
    on_board = {login for login, _ in prev.get("boards", {}).get("gear", [])}
    for login, gs in profile_scores(snap).items():
        if login in players and login not in on_board:
            players[login]["gs"] = gs
    return {**prev, "players": players, "details": details, "watch": watch,
            "days": {**prev.get("days", {}), **snap.get("days", {})},
            "sweep_after": snap.get("sweep_after", prev.get("sweep_after", ""))}


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


# Which stats a role's fighters are counted by, and what they did with them (0.27.0): the tank by defense (and the
# damage taken), the fighter by attack (damage) and defense, the supporter by support (boost) and defense.
STAT_PAIRS = {"TANK": (("def", "damageTaken"),), "FIGHTER": (("atk", "damage"), ("def", None)),
              "SUPPORT": (("sup", "boosted"), ("def", None))}
STAT_STEP = 10


def player_stats(state: dict) -> dict[str, dict]:
    """Attack, defense and support of every player the state knows: from the gear of a kept profile (it has upgrades
    and stones), else what the last reading gave (a profile, or the board without upgrades)."""
    out = {login: {k: d.get(k) for k in ("atk", "def", "sup")} for login, d in state.get("details", {}).items()}
    for login, w in state.get("watch", {}).items():
        rows = [v for v in (w.get("slots") or {}).values() if len(v) > 5]
        if rows:
            out[login] = {k: sum(v[i] or 0 for v in rows) for k, i in (("atk", 3), ("def", 4), ("sup", 5))}
    return out


def stat_digest(d: dict, stats: dict[str, dict]) -> dict | None:
    """A finished fight's fighters counted by role and by their stats in steps of STAT_STEP: per role, stat and step
    [fighters, fallen, sum of what they did]. Counts and sums only, no names; fighters with unknown stats are left
    out. None for a fight nobody fought in (a story without a fight)."""
    out: dict = {}
    for f in d.get("fighters") or []:
        known = stats.get((f.get("login") or "").lower())
        for stat, did in STAT_PAIRS.get(f.get("role"), ()):
            if not known or known.get(stat) is None:
                continue
            row = out.setdefault(f["role"], {}).setdefault(stat, {}).setdefault(
                str(known[stat] // STAT_STEP * STAT_STEP), [0, 0, 0])
            row[0] += 1
            row[1] += not f.get("alive")
            row[2] += (f.get(did) or 0) if did else 0
    return out or None


def record(snap: dict, prev: dict, cur: dict, t: int) -> dict:
    """One line of history: only what changed since `prev`, plus new fights."""
    rec: dict = {"t": t}
    for key in ("players", "details", "guilds", "channels", "rules", "watch"):
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
    if snap.get("details"):
        stats = player_stats(cur)
        for i, d in snap["details"].items():
            if sx := stat_digest(d, stats):
                extra[i]["sx"] = sx
    seen = set(prev.get("live_seen", []))
    for e in snap.get("live") or []:
        if e.get("archiveId") in live_ids(snap) and e["archiveId"] not in seen:
            extra[e["archiveId"]] = {**extra.get(e["archiveId"], {}), **live_digest(e)}
    if extra:
        rec["fightx"] = extra
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--watchlist", type=Path, default=Path("watchlist.txt"))
    ap.add_argument("--full-top", action="store_true", help="read the top 100 in this run even if it was read today")
    ap.add_argument("--part", choices=("all", "core", "profiles"), default="all",
                    help="core: everything but the profiles (the page is published after it); profiles: only those")
    args = ap.parse_args()
    now = datetime.now(BERLIN)
    site = Site()
    state_file = args.data / "state.json"
    prev = json.loads(state_file.read_text("utf-8")) if state_file.exists() else {}
    if args.part == "profiles" and not prev.get("boards"):
        print("Noch kein Stand, keine Profile zu lesen.")
        return 0
    try:
        today = f"{now:%Y-%m-%d}"
        snap = snapshot(site, read_watchlist(args.watchlist), prev.get("detail_last", 0),
                        {n: today for n in DAILY if prev.get("days", {}).get(n) != today and args.part != "profiles"},
                        prev.get("sweep_after", ""),
                        today if args.full_top or prev.get("days", {}).get("top") != today else "",
                        args.part, prev)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        # The site is down or busy: skip this run instead of failing (and retrying) on every schedule.
        print(f"Seite nicht erreichbar, Lauf übersprungen: {exc}")
        return 0
    cur = profiles_state(snap, prev) if args.part == "profiles" else state_from(snap, prev)
    rec = record(snap, prev, cur, int(now.timestamp()))
    rec["req"] = site.requests  # the site shows the load it puts on the game
    if args.part == "profiles":
        rec["part"] = "profiles"  # the second half of a run: not another run, its requests add to the run's
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
