"""Collector: one snapshot of the game's public data, stored as the changes since the last one.

Runs every 15 minutes in GitHub Actions during the game's play window. Reads only public endpoints (no login,
no cookies) and never sends anything but GETs. One run is about sixteen requests plus one per new fight and a
slice of the active players' profiles (about 55, so every active player is read about once a day), two seconds
apart; once a day come the compendium and the first kills (one each) and the changelog (three).
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
BOUND_SOURCES = ("PERSONAL_SHOP", "AUCTION", "TRADER", "SEALED")  # bound to the player, not for the market
SWEEP_RUNS = 60  # the active players' profiles are read in this many slices, so each one about once a day
# The site's four rankings (`by=` value -> the value they rank by). Others (silver, level) just return the gear board.
BOARD_FIELDS = {"gear": "gearScore", "gold": "silver", "errungenschaften": "achievements", "quests": "quests"}


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

    def text(self, path: str) -> str:
        """A page or script of the site itself (not the JSON API)."""
        return self.fetch(path, "*/*").decode("utf-8")


def read_watchlist(path: Path) -> list[str]:
    if not path.exists():
        return []
    names = (line.split("#")[0].strip().lower() for line in path.read_text("utf-8").splitlines())
    return sorted({n for n in names if n})


def parse_changelog(js: str) -> list[dict]:
    """The changelog page's entries ([{date, title, groups: [{title, items}]}], newest first) from its script
    chunk, where they sit as a JS literal with backtick strings and bare keys: turned into JSON piece by piece."""
    start = js.find("[{date:`")
    if start < 0:
        raise ValueError("keine Changelog-Einträge im Skript")
    out, code, depth, i = [], "", 0, start
    while True:
        c = js[i]
        if c == "`":
            end = i + 1
            while js[end] != "`":
                end += 2 if js[end] == "\\" else 1
            out.append(re.sub(r"([{,])(\w+):", r'\1"\2":', code))  # bare keys, only outside strings
            out.append(json.dumps(js[i + 1:end].replace("\\`", "`")))
            code, i = "", end + 1
            continue
        code += c
        depth += (c in "[{") - (c in "]}")
        i += 1
        if depth == 0:
            out.append(re.sub(r"([{,])(\w+):", r'\1"\2":', code))
            return json.loads("".join(out))


def read_changelog(site: Site) -> list[dict]:
    """The game's changelog. It has no API: it is built into the /changelog page's script, found via the router in
    the site's entry script (three requests)."""
    entry = re.search(r'<script[^>]+src="(/_nuxt/[\w.-]+\.js)"', site.text("/"))
    router = site.text(entry[1]) if entry else ""
    chunk = re.search(r"path:`/changelog`,component:\(\)=>\w+\(\(\)=>import\(`\./([\w.-]+\.js)`", router)
    if not chunk:
        raise ValueError("Changelog-Seite nicht gefunden")
    return parse_changelog(site.text("/_nuxt/" + chunk[1]))


# Reference data read once a day (on the first run of a day that has not got it): name -> how to read it.
DAILY = {"compendium": lambda site: site.get("/api/compendium"),
         "first_kills": lambda site: site.get("/api/guilds/first-kills"),
         "changelog": read_changelog}


def sweep_batch(logins: list[str], after: str, runs: int = SWEEP_RUNS) -> list[str]:
    """The next slice of `logins` (sorted) after the login the last run ended with; wraps around at the end."""
    ordered = sorted(set(logins))
    size = -(-len(ordered) // runs)
    rest = [x for x in ordered if x > after]
    return (rest + [x for x in ordered if x <= after])[:size]


def snapshot(site: Site, watchlist: list[str], detail_after: int = 0, daily: dict[str, str] | None = None,
             sweep_after: str = "") -> dict:
    """Everything one run asks the site, in the site's own shapes. Fights newer than `detail_after` also cost one
    request for their detail page (the archive's own numbers: who fell, roles, damage). `daily` maps the reference
    data that is due (the game's compendium, the guilds' first kills, its changelog; they hardly ever change) to
    today's date; what was read lands in the snapshot with its date in `days`. The board (top 100) and the watchlist
    give the plain gear score anyway; of the other active guild members a slice (after the login `sweep_after`) gets
    its profile read, since only the profile (attack + defense + support) has it."""
    snap: dict = {"guilds": {}, "watch": {}, "details": {}, "sweep": {}}
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
    snap["rules"] = site.get("/api/rules")
    for name, day in (daily or {}).items():
        try:
            snap[name] = DAILY[name](site)
            snap.setdefault("days", {})[name] = day
        except urllib.error.HTTPError as exc:  # an extra: a failing page must not cost the rest of the run
            exc.close()
        except (urllib.error.URLError, TimeoutError, ValueError, IndexError):
            pass
    for login in watchlist:
        try:
            snap["watch"][login] = site.get(f"/api/players/{quote(login)}")
        except urllib.error.HTTPError as exc:
            exc.close()
            if exc.code != 404:
                raise
    known = {r["login"].lower() for r in snap["boards"]["gear"]} | set(watchlist)
    due = sweep_batch([m["login"].lower() for page in snap["guilds"].values() for m in page.get("members") or []
                       if m.get("active") and m["login"].lower() not in known], sweep_after)
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


def price_value(text: str | None) -> int | None:
    """"4545 Gold 20 Silber" -> 454520 (silver), None when there is no price."""
    m = re.fullmatch(r"\s*(?:(\d+) Gold)?\s*(?:(\d+) Silber)?\s*", text or "")
    return int(m[1] or 0) * 100 + int(m[2] or 0) if m and (m[1] or m[2]) else None


SCENE = re.compile(r"^Szene (\d+)/(\d+): (.*)$")
CHOICE = re.compile(r"^Der Chat wählt \u201e(.+?)\u201c \((\d+) von (\d+)\): (.*)$")
OUT = re.compile(r" ?Ausgeschieden: ([^.]*)\.")
MORE = re.compile(r" und (\d+) weitere$")
DANGER = re.compile(r" ?Die Gefahr steigt auf (\d+)\.")
LIFE = re.compile(r" ?Alle verlieren (\d+) % Leben\.")
PAY = re.compile(r" ?Je Kopf (\d+) Silber (weniger|mehr)(?: am Ende)?\.")


def story_digest(log: list[str]) -> list[list] | None:
    """The scenes of a story adventure from its log: [text, choice, votes, total, result, out, danger, life,
    silver, fight] per scene. The names of those who dropped out are counted, never kept."""
    scenes: list[list] = []
    for line in log:
        if m := SCENE.match(line):
            scenes.append([m[3], None, 0, 0, "", 0, None, 0, 0, False])
        elif (m := CHOICE.match(line)) and scenes:
            text, row = m[4], scenes[-1]
            if o := OUT.search(text):
                names = o[1]
                row[5] = (int(more[1]) if (more := MORE.search(names)) else 0) + \
                    len(re.split(r", | und ", MORE.sub("", names)))
                text = OUT.sub("", text)
            if d := DANGER.search(text):
                row[6] = int(d[1])
                text = DANGER.sub("", text)
            if lf := LIFE.search(text):
                row[7] = int(lf[1])
                text = LIFE.sub("", text)
            if pay := PAY.search(text):
                row[8] = int(pay[1]) * (1 if pay[2] == "mehr" else -1)
                text = PAY.sub("", text)
            if text.endswith("Kampf!"):
                row[9], text = True, text[:-len("Kampf!")]
            row[1:5] = [m[1], int(m[2]), int(m[3]), text.strip()]
    return [r for r in scenes if r[1]] or None


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
    story = story_digest(d.get("log") or []) if d.get("kind") == "ADVENTURE" else None
    # Whose fight it was: the guild it is about (a raid on its treasury, a boss it summoned), the summoner's channel
    # and what the treasury lost or won (the game's text, parsed). Only what the page has.
    guild = {k: v for k, v in (("gn", d.get("guildName")), ("by", d.get("summonedBy")),
                               ("gc", silver_value(d.get("treasuryChange"))),
                               ("go", True if d.get("guildOnly") else None)) if v is not None}
    return {**({"story": story} if story else {}), **guild, "roles": n, "dead": dead, "rsum": by_role,
            "dmg": tally.get("damage"), "taken": tally.get("taken"), "heal": tally.get("healing"),
            "boost": tally.get("boosted"),
            "round": d.get("round"), "rounds": d.get("maxRounds"), "hp": d.get("hp"), "maxhp": d.get("maxHp"),
            "pay": [mean(pay[True]), mean(pay[False])]}


def live_digest(e: dict) -> dict:
    """The live view of a just finished fight has what the archive lacks: average gear and power, the
    recommendation and the fight engine's numbers. Only the fight the site still shows."""
    b = e.get("battle") or {}
    return {"gear": e.get("averageGear"), "power": e.get("averagePower"), "rec": e.get("recommendedGear"),
            "min": e.get("minGear"), "verdict": e.get("verdict"), "secs": b.get("secondsFought"),
            "enraged": b.get("enraged"), "gs": b.get("groupStrength"), "gsmax": b.get("groupStrengthMax"),
            "tanks": [b.get("tanksStanding"), b.get("tanksTotal")]}


def compendium_state(c: dict) -> dict:
    """The reference data worth showing: no icons, examples, intro texts or the stale Mythic fields."""
    pick = lambda rows, *keys: [{k: r.get(k) for k in keys} for r in rows or []]  # noqa: E731
    return {"potions": pick(c.get("potions"), "kind", "label", "description", "use"),
            "tiers": pick(c.get("tiers"), "tier", "material", "templates", "sources"),
            "bosses": [{**{k: b.get(k) for k in ("name", "lootTierMin", "lootTierMax", "gearTier", "recommendedGear",
                                                 "hidden", "unlockedBy")},
                        "hoard": pick(b.get("hoard"), "name", "slot")} for b in c.get("bosses") or []],
            "fights": pick(c.get("fights"), "name", "kind", "kindLabel", "difficulty"),
            "projects": pick(c.get("projects"), "project", "label", "description", "nextBattle"),
            "workshop": workshop_state(c.get("workshop") or {})}


def workshop_state(w: dict) -> dict:
    """The Schmiede's levels (highest seal tier, the boss the guild must have beaten, seals per piece) and the
    Lager's wares with the Lager level that unlocks them."""
    pick = lambda rows, *keys: [{k: r.get(k) for k in keys} for r in rows or [] if isinstance(r, dict)]  # noqa: E731
    return {"forge": pick(w.get("forge"), "level", "upTo", "upToTier", "requires", "sealsPerItem"),
            "wares": pick(w.get("wares"), "kind", "label", "description", "level", "price"),
            "sealSalePerTier": w.get("sealSalePerTier")}


def first_kills_state(rows) -> list[list]:
    """The guilds' first kills as [boss, level, guild login, guild name, time, boss order], in the game's order."""
    return [[r.get("bossName"), r.get("level"), r.get("guildLogin"), r.get("guildName"), r.get("at"),
             r.get("bossOrder")] for r in rows if isinstance(r, dict)] if isinstance(rows, list) else []


def guild_state(page: dict) -> dict:
    g, boss = page.get("guild") or {}, page.get("boss") or {}
    buildings = {b["key"]: [b.get("level"), b.get("maxLevel"), b.get("label"), b.get("effect"),
                            price_value(b.get("nextPrice")), b.get("nextEffect"), b.get("blocker")]
                 for b in page.get("buildings") or []}
    bosses = {b["name"]: [b.get("highestWon"), b.get("nextPriceSilver"), b.get("nextRecommendedGear")]
              for b in boss.get("bosses") or []}
    return {"name": g.get("name"), "treasury": g.get("treasurySilver"), "members": g.get("members"),
            "active": g.get("activeMembers"), "gear": g.get("gearScore"), "raid": g.get("raidLevel"),
            "boss_wins": boss.get("wins"), "boss_losses": boss.get("losses"), "boss_gear": boss.get("averageGear"),
            "buildings": buildings, "bosses": bosses}


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
    watch: dict[str, dict] = {}
    for login, p in snap["watch"].items():
        slots = {s["slot"]: [s.get("label"), i.get("name"), i.get("tier"), i.get("attack"), i.get("defense"),
                             i.get("support"), i.get("durability"), int(i.get("source") in BOUND_SOURCES),
                             i.get("socket")]
                 if (i := s.get("item")) else [s.get("label")]
                 for s in p.get("slots") or []}
        watch[login] = {"survival": p.get("survivalPercent"), "life": p.get("life"),
                        "ach": p.get("achievementsUnlocked"), "stats": p.get("stats") or {}, "slots": slots}
        details[login] = {**details.get(login, {}), "atk": p.get("attack"), "def": p.get("defense"),
                          "sup": p.get("support"), "silver": p.get("silver")}
        if login not in players:
            players[login] = {**prev.get("players", {}).get(login, {}), "name": p.get("displayName"),
                              "guild": (p.get("guild") or {}).get("login")}
    # The plain gear score (attack + defense + support): the profiles give it, the board its own value for the
    # top 100 (so its order makes sense); a player not read this run keeps the last one.
    scores: dict[str, int] = {}
    for login, p in {**snap.get("sweep", {}), **snap["watch"]}.items():
        if all(p.get(k) is not None for k in ("attack", "defense", "support")):
            scores[login] = p["attack"] + p["defense"] + p["support"]
    scores.update({r["login"].lower(): r["gearScore"] for r in snap["boards"].get("gear", [])
                   if r.get("gearScore") is not None})
    for login, p in players.items():
        if (gs := scores.get(login, prev.get("players", {}).get(login, {}).get("gs"))) is not None:
            p["gs"] = gs
    # Seen before but in no guild and on no board now: left their guild. The last gear score stays known.
    for login, old in prev.get("players", {}).items():
        if login not in players:
            players[login] = {**old, "guild": None, "active": None}
    return {"players": players, "details": {**prev.get("details", {}), **details}, "boards": boards,
            "guilds": guilds, "watch": watch,
            "channels": {c["login"]: bool(c.get("live")) for c in snap["channels"] if c.get("enabled")},
            "chat": {c["login"]: c.get("chatMode") for c in snap["channels"] if c.get("enabled")},
            "rules": {k: v for k, v in (snap.get("rules") or {}).items() if k != "playWindowOpenNow"},
            "compendium": (compendium_state(snap["compendium"]) if snap.get("compendium")
                           else prev.get("compendium", {})),
            "first_kills": (first_kills_state(snap["first_kills"]) if "first_kills" in snap
                            else prev.get("first_kills", [])),
            "changelog": snap["changelog"] if snap.get("changelog") else prev.get("changelog", []),
            "days": {**prev.get("days", {}), **snap.get("days", {})},
            "fight_last": max([prev.get("fight_last", 0), *(f.get("id", 0) for f in snap["fights"])]),
            "sweep_after": snap.get("sweep_after", prev.get("sweep_after", "")),
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
    for key in ("players", "details", "guilds", "channels", "chat", "rules", "watch"):
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
        today = f"{now:%Y-%m-%d}"
        snap = snapshot(site, read_watchlist(args.watchlist), prev.get("detail_last", 0),
                        {n: today for n in DAILY if prev.get("days", {}).get(n) != today},
                        prev.get("sweep_after", ""))
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
