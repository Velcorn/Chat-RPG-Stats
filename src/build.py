"""Build: replay the collected history and write the JSON files the dashboard reads.

Reads data/days/*.jsonl (one line of changes per run, see collect.py) and data/state.json, writes
<out>/data/summary.json, <out>/data/players.json and one <out>/data/p/<login>.json per player.
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import shutil
import statistics
import time
import tomllib
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import collect
import fightstats
from finale import abspann, finale
from observed import observed
from timelapse import timelapse, top_lapse

DAY = 86400
BOARD_LAG = 12 * 3600  # the board shows the plain gear score only a few frames after GEAR_SINCE
BOARD_GRID = 2 * 3600  # the top-100 time lapse has a frame every two hours
PEERS_MIN = 8
PEERS_CLASS_MIN = 20  # class peers for the stat bars: within 10 % of the gear score, else this many nearest
PEERS_BAND = 4  # class peers from which on the stat bars show the band (10 % to 90 %)
FINAL_BOSS_AT = datetime(2026, 10, 28, 18, 0, tzinfo=ZoneInfo("Europe/Berlin")).isoformat()  # announced by the game


def replay(days: Path):
    for f in sorted(days.glob("*.jsonl")):
        for line in f.read_text("utf-8").splitlines():
            if line.strip():
                yield json.loads(line)


class History:
    """Change points per player, guild and board, rebuilt from the day files."""

    def __init__(self, records):
        self.gs: dict[str, list] = defaultdict(list)         # login -> [[t, gear score], ...] (only changes)
        self.power: dict[str, list] = defaultdict(list)      # login -> [[t, Kampfkraft], ...] (only changes)
        self.guild: dict[str, list] = defaultdict(list)      # login -> [[t, guild login or None], ...]
        self.details: dict[str, list] = defaultdict(list)    # login -> [[t, {atk, def, sup, silver, quests}], ...]
        self.rank: dict[str, list] = defaultdict(list)       # login -> [[t, rank on the gear board or None], ...]
        self.border: list[list] = []                         # [[t, gear score of place 100], ...] (only changes)
        self.guilds: dict[str, list] = defaultdict(list)     # guild -> [[t, treasury, members, active, gear], ...]
        self.fights: list[dict] = []
        self.fightx: dict[int, dict] = defaultdict(dict)  # fight id -> detail and live digests (since 0.9.0)
        self.window: list[list] = []                         # [[t, from, to], ...] the play window, at every change
        self.rules_log: list[list] = []                      # [[t, rule, old, new], ...] (since 0.10.0)
        self.live_runs: dict[str, list] = defaultdict(lambda: [0, 0])  # channel -> [runs live, runs seen]
        self.leader: list[list] = []                         # [[t, login of place 1], ...] (only changes)
        self.top_score: list[list] = []                      # [[t, gear score of place 1], ...] (only changes)
        self.board_last: list = []                           # [[login, score], ...] of the latest gear board
        self.board_at: dict[int, list] = {}                  # grid time -> [[login, score], ...] of the gear board then
        self.first = self.last = None
        self.runs = 0
        self.requests = None  # requests of the latest run (recorded since 0.8.4)
        board: list[str] = []
        board_scores: list = []
        next_grid = None
        guild_now: dict[str, dict] = {}
        rules_now: dict = {}
        live_now: dict[str, bool] = {}
        for rec in records:
            if rec.get("part") == "backfill":  # digests of older fights (backfill.py): no run, no point in time
                for fid, digest in rec.get("fightx", {}).items():
                    self.fightx[int(fid)].update(digest)
                continue
            t = rec["t"]
            self.first = self.first or t
            self.last = t
            next_grid = next_grid or -(-t // BOARD_GRID) * BOARD_GRID
            while next_grid <= t:  # the board as it stood at each grid time (before this record changed it)
                if board_scores:
                    self.board_at[next_grid] = board_scores
                next_grid += BOARD_GRID
            if rec.get("part") == "profiles":  # the second half of a run: its requests add to the run's
                self.requests = (self.requests or 0) + rec.get("req", 0)
            else:
                self.runs += 1
                self.requests = rec.get("req", self.requests)
            for login, p in rec.get("players", {}).items():
                for series, key in ((self.gs, "gs"), (self.power, "gear"), (self.guild, "guild")):
                    if key in p and (p[key] is not None or key == "guild"):  # a record only has changed fields
                        put(series[login], t, p[key])
            for login, d in rec.get("details", {}).items():
                self.details[login].append([t, d])
            if "gear" in rec.get("boards", {}):
                board_scores = self.board_last = rec["boards"]["gear"]
                if board_scores:
                    put(self.leader, t, board_scores[0][0])
                    put(self.top_score, t, board_scores[0][1])
                new = [login for login, _ in rec["boards"]["gear"]]
                for login in set(board) - set(new):
                    put(self.rank[login], t, None)
                for i, login in enumerate(new):
                    put(self.rank[login], t, i + 1)
                board = new
                if len(new) >= 100:
                    put(self.border, t, rec["boards"]["gear"][99][1])
            for g, v in rec.get("guilds", {}).items():
                full = guild_now[g] = {**guild_now.get(g, {}), **v}
                self.guilds[g].append([t, *(full.get(k) for k in ("treasury", "members", "active", "gear"))])
            for rule, v in rec.get("rules", {}).items():
                if rule in rules_now and rules_now[rule] != v:
                    self.rules_log.append([t, rule, rules_now[rule], v])
                rules_now[rule] = v
            if "playWindowFrom" in rules_now and "playWindowTo" in rules_now:
                span = [rules_now["playWindowFrom"], rules_now["playWindowTo"]]
                if not self.window or self.window[-1][1:] != span:
                    self.window.append([t, *span])
            live_now.update(rec.get("channels", {}))
            for channel, live in ({} if rec.get("part") == "profiles" else live_now).items():
                self.live_runs[channel][0] += bool(live)
                self.live_runs[channel][1] += 1
            self.fights += rec.get("fights", [])
            for fid, digest in rec.get("fightx", {}).items():
                self.fightx[int(fid)].update(digest)


def put(series: list, t: int, v) -> None:
    if not series or series[-1][1] != v:
        series.append([t, v])


def value_at(series: list, t: float):
    """The value at time `t`, or None if the series starts later."""
    i = bisect.bisect_right([p[0] for p in series], t)
    return series[i - 1][1] if i else None


def change(series: list, now: float, span: float):
    """Change over the last `span` seconds, None without data that old."""
    then = value_at(series, now - span)
    cur = series[-1][1] if series else None
    return None if then is None or cur is None else cur - then


GEAR_SINCE = 1791151200  # 2026-10-04 22:00 UTC: from here the board shows the plain gear score (before: Kampfkraft)


def gain(series: list, now: float, span: float, lookback: float = 7 * DAY, since: float | None = None):
    """How far the value is above its own peak before the last `span` seconds (looking back `lookback` more), 0 if it
    isn't. A value that dips and returns (08./09.10.2026: some profiles read 0 to 60 % of their gear for a while)
    isn't a rise: the change from the dip would be the day's biggest. Values before `since` are another measure
    (their peaks would hide every rise). None without data that old."""
    since = GEAR_SINCE if since is None else since
    cur = series[-1][1] if series else None
    start = value_at(series, now - span) if now - span >= since else None
    if start is None or cur is None:
        return None
    from_ = max(now - span - lookback, since)
    carried = value_at(series, from_) if from_ == now - span - lookback else None  # the value when the look-back began
    before = [v for t, v in series if from_ < t <= now - span and v is not None]
    return max(0, cur - max([start, carried or 0, *before]))


def pace(series: list, now: float, span: float = 7 * DAY) -> float | None:
    """Gear points per day over the last `span` (or since the first data point, if at least 12 h ago)."""
    if not series:
        return None
    start = max(now - span, series[0][0])
    if now - start < DAY / 2:
        return None
    then, cur = value_at(series, start), series[-1][1]
    return None if then is None or cur is None else (cur - then) / ((now - start) / DAY)


def rounded(x, n=2):
    return None if x is None else round(x, n)


def season_manifest(data: Path) -> dict:
    """Published season index. It stays useful before the first season has been archived."""
    try:
        manifest = json.loads((data / "seasons.json").read_text("utf-8"))
        if not isinstance(manifest.get("archives"), list):
            raise ValueError
        return manifest
    except (OSError, ValueError, TypeError):
        return {"current": {"id": "current", "label": "Aktuelle Saison"}, "archives": []}


def publish_archives(data: Path, target: Path, manifest: dict) -> None:
    """Copy immutable generated season data from the data branch into the Pages artifact."""
    write(target / "seasons.json", manifest)
    source = data / "seasons"
    if source.exists():
        shutil.copytree(source, target / "seasons", dirs_exist_ok=True)


def gear_key(players: dict, details: dict):
    """Sort key in the game's order: gear score, equal scores by silver (known for the board and the watchlist)."""
    return lambda login: (-(players[login].get("gs") or 0), -(details.get(login, {}).get("silver") or 0))


def board_gap(i: int, scores: list, rows: list) -> dict | None:
    """The distance to the next place: behind the player above, for the leader ahead of the second place. The board
    orders equal scores by silver, so a tie is measured in silver, else in score points."""
    j = i - 1 if i else 1
    if j >= len(rows) or scores[i] is None or scores[j] is None:
        return None
    if scores[i] != scores[j]:
        return {"ahead": i == 0, "tie": False, "amount": abs(scores[j] - scores[i])}
    mine, other = rows[i].get("silver"), rows[j].get("silver")
    if mine is None or other is None:
        return None
    return {"ahead": i == 0, "tie": True, "amount": abs(other - mine)}


def build(data: Path, out: Path, now: float | None = None, include_archives: bool = True) -> dict:
    h = History(replay(data / "days"))
    state = json.loads((data / "state.json").read_text("utf-8"))
    now = now or h.last or time.time()
    manifest = season_manifest(data)
    players, details, guilds = state["players"], state["details"], state["guilds"]
    gear = {login: p["gs"] for login, p in players.items() if p.get("gs") is not None}
    order = sorted(gear.values(), reverse=True)

    gear_order = gear_key(players, details)

    def rank(g):  # ties share a rank
        return bisect.bisect_left([-x for x in order], -g) + 1

    paces = {login: pace(h.gs[login], now) for login in gear}
    day = {login: change(h.gs[login], now, DAY) for login in gear}
    week = {login: change(h.gs[login], now, 7 * DAY) for login in gear}
    board = [login for login, _ in state["boards"].get("gear", [])]
    ranks_24h = {login: value_at(h.rank[login], now - DAY) for login in board}
    top100_gear = gear.get(board[-1]) if len(board) >= 100 else None
    tail_paces = [paces[x] for x in board[89:100] if paces.get(x) is not None]
    top100_pace = statistics.median(tail_paces) if tail_paces else None

    def row(login):
        p = players[login]
        return {"login": login, "name": p.get("name") or login, "gear": p.get("gs"), "guild": p.get("guild"),
                "day": day.get(login), "week": week.get(login), "pace": rounded(paces.get(login)),
                "silver": details.get(login, {}).get("silver")}

    def risers(span):
        gains = {login: gain(h.gs[login], now, span) for login in gear}
        best = sorted((login for login in gains if gains[login]), key=lambda x: -gains[x])[:25]
        return [{**row(login), "gain": gains[login]} for login in best]

    # The border before the board showed the plain gear score (Kampfkraft then) would be a different measure.
    border_series = [p for p in h.border if p[0] >= GEAR_SINCE + BOARD_LAG]
    board_rows = []
    for i, login in enumerate(board):
        prev = ranks_24h.get(login)
        board_rows.append({**row(login), "rank": i + 1, "rank_change": None if prev is None else prev - (i + 1),
                           **{k: details.get(login, {}).get(k) for k in ("atk", "def", "sup")}})
    scores = [score for _, score in state["boards"].get("gear", [])]
    for i, r in enumerate(board_rows):
        r["gap"] = board_gap(i, scores, board_rows)

    # The roles of the top places, read from the main stat of the gear (the game doesn't publish the chosen role):
    # {"top": n, "n": players with a known split, "tank": .., "fighter": .., "support": ..} for the top 10/25/50/100.
    role_of = {"def": "tank", "atk": "fighter", "sup": "support"}
    top_roles = []
    for top in (10, 25, 50, 100):
        known = [r for r in board_rows[:top] if all(r[k] is not None for k in ("atk", "def", "sup"))]
        top_roles.append({"top": top, "n": len(known), "tank": 0, "fighter": 0, "support": 0})
        for r in known:
            top_roles[-1][role_of[main_stat(r)]] += 1

    # The Kampfkraft ranking (gear plus talents): the game ranks by the gear score, but its guild pages give the
    # Kampfkraft of every member, so this is the top 100 of everyone known, not only of the game's board.
    power = {login: p["gear"] for login, p in players.items() if p.get("gear") is not None}
    by_power = sorted(power, key=lambda x: (-power[x], -(details.get(x, {}).get("silver") or 0)))  # ties: silver
    power_rows = [{**row(login), "rank": i + 1, "power": power[login],
                   "power_day": change(h.power[login], now, DAY)}
                  for i, login in enumerate(by_power[:100])]
    for i, r in enumerate(power_rows):
        r["gap"] = board_gap(i, [x["power"] for x in power_rows], power_rows)

    guild_members: dict[str, list[str]] = defaultdict(list)
    for login, p in players.items():
        if p.get("guild"):
            guild_members[p["guild"]].append(login)
    guild_rows = []
    for g, info in guilds.items():
        if not info.get("members"):  # a guild without members has no page of its own, only boss wins (`guild_boss`)
            continue
        members = guild_members.get(g, [])
        active_gear = [players[m]["gs"] for m in members
                       if players[m].get("active") and players[m].get("gs") is not None]
        gear_series = [[r[0], r[4]] for r in h.guilds.get(g, []) if r[4] is not None]
        treasury_series = [[r[0], r[1]] for r in h.guilds.get(g, []) if r[1] is not None]
        guild_rows.append({"login": g, **info, "day": change(gear_series, now, DAY),
                           "week": change(gear_series, now, 7 * DAY),
                           "treasury_week": change(treasury_series, now, 7 * DAY),
                           "avg_gear": rounded(statistics.mean(active_gear), 1) if active_gear else None,
                           "donated": sum(players[m].get("donated") or 0 for m in members),
                           "top": [row(m) for m in sorted(members, key=gear_order)[:10]],
                           "donors": [{**row(m), "donated": players[m].get("donated")}
                                      for m in sorted(members, key=lambda m: -(players[m].get("donated") or 0))[:10]],
                           "series": h.guilds.get(g, [])})

    boss_rec = state.get("boss_rec", {})
    pay_rows = fightstats.payout_rows(h.fights, h.fightx)
    loot_rows = fightstats.loot_rows(h.fights, h.fightx)
    summary_stats = fightstats.fight_stats(h.fights, h.fightx, now, boss_rec=boss_rec)
    summary = {"generated": int(now), "version": project_version(), "since": h.first, "runs": h.runs,
               "season": {**manifest.get("current", {}), "start": h.first, "end": None, "archived": False},
               "load": {"per_run": h.requests,
                        "runs_per_day": collect.RUNS_PER_DAY},
               "players": len(players),
               "ranked": len(gear),
               "active": sum(1 for p in players.values() if p.get("active")),
               "board": board_rows, "power_board": power_rows,
               "risers": {"day": risers(DAY), "week": risers(7 * DAY)},
               "top100": {"gear": top100_gear, "pace": rounded(top100_pace), "series": border_series,
                          "roles": top_roles},
               "guilds": sorted(guild_rows, key=lambda g: -(g.get("gear") or 0)),
               "final_boss_at": FINAL_BOSS_AT,
               "fights": {"recent": recent_fights(h),
                          "total": len(h.fights)},
               "stats": summary_stats,
               "eras": {"after": fightstats.fight_stats(h.fights, h.fightx, now, lo=fightstats.UPDATE,
                                                        boss_rec=boss_rec),
                        "before": fightstats.fight_stats(h.fights, h.fightx, now, hi=fightstats.UPDATE,
                                                         boss_rec=boss_rec)},
               "payout": fightstats.payout(pay_rows),
               "loot": fightstats.loot(loot_rows),
               "guild_fights": fightstats.guild_fights(h.fights, h.fightx, now),
               "stat_curves": fightstats.stat_curves(h.fights, h.fightx, now, boss_rec=boss_rec),
               "win_odds": fightstats.win_odds(h.fights, h.fightx, now, boss_rec=boss_rec),
               "first_kills": state.get("first_kills", []),
               "channels": state.get("channels", {}),
               "channel_stats": channel_stats(h, state, summary_stats["channels"]),
               "rules": {"now": state.get("rules", {}), "log": h.rules_log[::-1][:60],
                         "since": h.first if state.get("rules") else None},
               "guild_boss": {"guilds": len(guilds), "wins": sum(g.get("boss_wins") or 0 for g in guilds.values()),
                              "losses": sum(g.get("boss_losses") or 0 for g in guilds.values())},
               "economy": economy(h, now),
               "finale": finale(h, players, GEAR_SINCE + BOARD_LAG),
               "abspann": abspann(h, {g["login"]: g for g in guild_rows})}

    target = out / "data"
    if target.exists():
        shutil.rmtree(target)
    (target / "p").mkdir(parents=True)
    write(target / "summary.json", summary)
    write(target / "changelog.json", parse_changelog(
        (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text("utf-8")))
    write(target / "players.json", [
        [login, p.get("name") or login, p["gs"], p.get("guild"), bool(p.get("active"))]
        for login, p in sorted(players.items(), key=lambda kv: gear_order(kv[0])) if p.get("gs") is not None])
    with_split = [x for x in gear if all(details.get(x, {}).get(k) is not None for k in ("atk", "def", "sup"))]
    # Every known split without names, for the build map: [attack, defense, support, gear score].
    write(target / "builds.json", [[details[x]["atk"], details[x]["def"], details[x]["sup"], gear[x]]
                                   for x in with_split])
    write(target / "observed.json", observed(state))
    write(target / "payout.json", pay_rows)
    (target / "payout.csv").write_text(fightstats.payout_csv(pay_rows), "utf-8")
    write(target / "loot.json", loot_rows)
    (target / "loot.csv").write_text(fightstats.loot_csv(loot_rows), "utf-8")
    if lapse := timelapse(h, players, h.border):
        write(target / "timelapse.json", lapse)
    if top := top_lapse(h, players):
        write(target / "toplapse.json", top)
    gear_sorted = sorted(gear.values())
    for login in gear:
        write(target / "p" / f"{login}.json", player_page(login, h, state, now, rank, paces, with_split,
                                                          top100_gear, top100_pace, guild_members,
                                                          gear_sorted))
    if include_archives:
        publish_archives(data, target, manifest)
    return summary


def recent_fights(h: History, n: int = 50) -> list[dict]:
    """The last fights, newest first, with the share that fell where the fight has a detail digest."""
    return [{**f, **fightstats.fallen(h.fightx.get(f["id"])), **fightstats.whose(h.fightx.get(f["id"]))}
            for f in h.fights[-n:][::-1]]


def channel_stats(h: History, state: dict, fights_by_channel: list[dict]) -> dict:
    """Per streamer: share of runs live, and the fight numbers of their channel."""
    fights = {c["channel"]: c for c in fights_by_channel}
    out = {}
    for login in state.get("channels", {}):
        live, seen = h.live_runs.get(login, [0, 0])
        f = fights.get(login, {})
        out[login] = {"live_share": rounded(100 * live / seen, 1) if seen else None,
                      "fights": f.get("n", 0), "wins": f.get("wins", 0), "fighters": f.get("fighters"),
                      "death": f.get("death_win")}
    return out


def economy(h: History, now: float, days: int = 30) -> dict:
    """Silver in the guild treasuries, one point per day."""
    treasuries = [[[r[0], r[1]] for r in rows if r[1] is not None] for rows in h.guilds.values()]
    points = []
    for k in range(days, -1, -1):
        t = now - k * DAY
        if h.first is None or t < h.first:
            continue
        points.append({"t": int(t), "treasury": sum(value_at(series, t) or 0 for series in treasuries)})
    return {"series": points}


BLIP = 6 * 3600  # an absence from the board this short is no gap in the rank line
DIP_SHARE = 0.05  # the share of the gear score lost at once that counts as a dip when it comes back within the hour
DIP_RANKS = 5  # ranks lost at once that count as a dip when they come back at the next run


def rank_series(series: list, since: float | None = None, blip: float = BLIP, dip_within: float = 3600) -> list:
    """The rank line of a player page: from the day the board shows plain gear (`GEAR_SINCE`; before, it ranked
    Kampfkraft, another order), without the runs off the board at its start and without short absences (at most
    `blip` seconds between two ranks: gear taken off for a while or a page read in the middle of an update). Longer
    ones stay gaps. A rank that falls by DIP_RANKS or more and is back at the next run (within `dip_within`) is
    dropped too."""
    since = GEAR_SINCE if since is None else since
    pts = [p for p in series if p[0] >= since]
    while pts and pts[0][1] is None:
        pts.pop(0)
    out = []
    for i, (t, v) in enumerate(pts):
        if v is None:
            back = next((q for q in reversed(pts[:i]) if q[1] is not None), None)
            ahead = next((q for q in pts[i + 1:] if q[1] is not None), None)
            if back and ahead and ahead[0] - back[0] <= blip:
                continue
        out.append([t, v])
    return [q for i, q in enumerate(out) if not is_dip(out, i, dip_within)]


def is_dip(pts: list, i: int, blip: float) -> bool:
    """Whether `pts[i]` is a rank that fell by DIP_RANKS or more and mostly recovered at the next point."""
    if not 0 < i < len(pts) - 1:
        return False
    (_, before), (t, v), (after_t, after) = pts[i - 1], pts[i], pts[i + 1]
    if None in (before, v, after) or after_t - t > blip:
        return False
    drop = v - before
    return drop >= DIP_RANKS and v - after >= drop / 2


def gear_series(series: list, share: float = DIP_SHARE, within: float = 3600) -> list:
    """The gear line of a player page without dips: a value that falls by `share` or more below the one before and is
    back to at least half way up within `within` seconds (a few runs) is gear taken off for a moment."""
    out, i = [], 0
    while i < len(series):
        t, v = series[i]
        before = out[-1][1] if out else None
        if before and v is not None and v <= before * (1 - share):
            back = next((j for j in range(i + 1, min(i + 4, len(series)))
                         if series[j][0] - t <= within and series[j][1] is not None
                         and series[j][1] >= before - (before - v) / 2), None)
            if back is not None:
                i = back
                continue
        out.append([t, v])
        i += 1
    return out


def parse_changelog(text: str) -> list[dict]:
    """Read dated releases with heading or bold-label groups; preserve item text."""
    entries = []
    group = None
    for line in text.splitlines():
        if match := re.fullmatch(r"## (\d{4}\.\d{2}\.\d{2}) \((\d{2}\.\d{2}\.\d{4})\)", line):
            entries.append({"version": match[1], "date": match[2], "groups": []})
            group = None
        elif entries:
            if match := re.fullmatch(r"(?:### (.+)|\*\*(.+)\*\*)", line):
                group = {"title": match[1] or match[2], "items": []}
                entries[-1]["groups"].append(group)
            elif line.startswith("- "):
                if group is None:
                    group = {"title": "", "items": []}
                    entries[-1]["groups"].append(group)
                group["items"].append(line[2:])
            elif line[:1].isspace() and line.strip() and group and group["items"]:
                group["items"][-1] += " " + line.strip()
    return sorted(entries, key=lambda entry: entry["version"], reverse=True)


def project_version() -> str | None:
    """The version in pyproject.toml (the page shows it behind its title), None if there is no such file."""
    path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    try:
        return tomllib.loads(path.read_text("utf-8"))["project"]["version"]
    except (OSError, KeyError, ValueError):
        return None


def main_stat(d: dict) -> str:
    """The largest of attack, defense and support (the first on a tie): what a player is built for."""
    return max(("atk", "def", "sup"), key=lambda k: d[k])


def class_peers(login: str, g: int, players: dict, details: dict, with_split: list) -> dict | None:
    """The players with the same main stat and a similar gear score (within 10 % or 10 points, else the nearest
    PEERS_CLASS_MIN): per stat the median and the band [10 %, 90 %] (from PEERS_BAND players on)."""
    main = main_stat(details[login])
    same = sorted((x for x in with_split if x != login and main_stat(details[x]) == main),
                  key=lambda x: abs(players[x]["gs"] - g))
    close = [x for x in same if abs(players[x]["gs"] - g) <= max(10, g * 0.1)]
    peers = close if len(close) >= PEERS_CLASS_MIN else same[:PEERS_CLASS_MIN]
    if not peers:
        return None
    out = {"main": main, "n": len(peers), "gear": round(statistics.mean(players[x]["gs"] for x in peers)),
           "med": {k: rounded(statistics.median(details[x][k] for x in peers), 1) for k in ("atk", "def", "sup")}}
    if len(peers) >= PEERS_BAND:
        out["band"] = {k: [rounded(q, 1) for q in statistics.quantiles([details[x][k] for x in peers], n=10,
                                                                         method="inclusive")[::8]]
                       for k in ("atk", "def", "sup")}
    return out


def player_page(login, h, state, now, rank, paces, with_split, top100_gear, top100_pace, guild_members,
                gear_sorted) -> dict:
    players, details = state["players"], state["details"]
    p = players[login]
    g = p["gs"]
    my_pace = paces.get(login)
    higher = sorted({x["gs"] for x in players.values() if x.get("gs") is not None and x["gs"] > g})
    next_gap = higher[0] - g + 1 if higher else None
    lower = max((x["gs"] for k, x in players.items() if k != login and x.get("gs") is not None and x["gs"] <= g),
                default=None)
    on_board = h.rank[login][-1][1] if h.rank.get(login) else None
    board = state["boards"].get("gear", [])
    place = next((i for i, (x, _) in enumerate(board) if x == login), None)
    gap = None if place is None else board_gap(place, [v for _, v in board],
                                               [{"silver": details.get(x, {}).get("silver")} for x, _ in board])
    forecast = {"rank": on_board or rank(g), "exact": on_board is not None, "next_gap": next_gap, "gap": gap,
                "next_days": rounded(next_gap / my_pace, 1) if next_gap and my_pace and my_pace > 0 else None,
                "top100_gap": None, "top100_days": None,
                "lead": g - lower if next_gap is None and lower is not None else None}
    if top100_gear is not None and g <= top100_gear:
        gap = top100_gear - g + 1
        forecast["top100_gap"] = gap
        edge = my_pace - (top100_pace or 0) if my_pace is not None else None
        forecast["top100_days"] = rounded(gap / edge, 1) if edge and edge > 0 else None

    # Peers: players with a known split and a similar gear score (the nearest ones, at least PEERS_MIN), for the pace.
    others = sorted((x for x in with_split if x != login), key=lambda x: abs(players[x]["gs"] - g))
    close = [x for x in others if abs(players[x]["gs"] - g) <= max(10, g * 0.05)]
    peers = close if len(close) >= PEERS_MIN else others[:PEERS_MIN]
    split = None
    if peers:
        split = {"n": len(peers), "gear": round(statistics.mean(players[x]["gs"] for x in peers))}
        split["pace"] = rounded(statistics.median(known)) if (known := [paces[x] for x in peers
                                                                          if paces.get(x) is not None]) else None
        # The marker on the stat bars compares within the class only (the same main stat: a tank's attack next to
        # fighters' says little): the median and, from PEERS_BAND players on, the band from 10 % to 90 %.
        if login in with_split:
            split["cls"] = class_peers(login, g, players, details, with_split)

    guild = None
    if p.get("guild"):
        members = sorted(guild_members[p["guild"]], key=lambda m: -(players[m].get("donated") or 0))
        pos = members.index(login)
        above = players[members[pos - 1]].get("donated") or 0 if pos else None
        by_gear = sorted(guild_members[p["guild"]], key=gear_key(players, details))
        info = state["guilds"].get(p["guild"], {})
        total = sum(players[m].get("donated") or 0 for m in members)
        guild = {"login": p["guild"], "name": info.get("name"), "members": len(members), "joined": p.get("joined"),
                 "donated": p.get("donated"), "donation_rank": pos + 1,
                 "donation_share": rounded(100 * (p.get("donated") or 0) / total, 2) if total else None,
                 "donation_gap": above - (p.get("donated") or 0) + 1 if above is not None else None,
                 "gear_rank": by_gear.index(login) + 1,
                 "gear_share": (rounded(100 * p["gear"] / info["gear"], 3)
                                if info.get("gear") and p.get("gear") else None)}

    watch = state.get("watch", {}).get(login)
    standing = {"better": rounded(100 * bisect.bisect_left(gear_sorted, g) / len(gear_sorted), 1),
                "of": len(gear_sorted)}
    return {"login": login, "standing": standing, "name": p.get("name") or login, "gear": g, "power": p.get("gear"),
            "guild": guild,
            "active": p.get("active"),
            "pace": rounded(my_pace), "day": change(h.gs[login], now, DAY),
            "week": change(h.gs[login], now, 7 * DAY), "forecast": forecast,
            "board_rank": on_board,
            "split": {k: details.get(login, {}).get(k) for k in ("atk", "def", "sup", "silver", "quests")},
            "peers": split,
            "series": {"gear": gear_series(h.gs[login]), "rank": rank_series(h.rank.get(login, [])),
                       "silver": [[t, d.get("silver")] for t, d in h.details.get(login, [])
                                  if d.get("silver") is not None]},
            "watch": watch or None}


def write(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), "utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, default=Path("_site"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(__file__).parent.parent / "site" / "index.html", args.out / "index.html")
    shutil.copytree(Path(__file__).parent.parent / "site" / "fonts", args.out / "fonts", dirs_exist_ok=True)
    summary = build(args.data, args.out)
    print(f"{summary['players']} Spieler, {summary['runs']} Läufe, {summary['fights']['total']} Kämpfe")


if __name__ == "__main__":
    main()
