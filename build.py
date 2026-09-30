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
from collections import defaultdict
from pathlib import Path

DAY = 86400
PEERS_MIN = 8


def replay(days: Path):
    for f in sorted(days.glob("*.jsonl")):
        for line in f.read_text("utf-8").splitlines():
            if line.strip():
                yield json.loads(line)


class History:
    """Change points per player, guild and board, rebuilt from the day files."""

    def __init__(self, records):
        self.gear: dict[str, list] = defaultdict(list)       # login -> [[t, gear], ...] (only changes)
        self.donated: dict[str, list] = defaultdict(list)
        self.guild: dict[str, list] = defaultdict(list)      # login -> [[t, guild login or None], ...]
        self.details: dict[str, list] = defaultdict(list)    # login -> [[t, {atk, def, sup, silver, quests}], ...]
        self.rank: dict[str, list] = defaultdict(list)       # login -> [[t, rank on the gear board or None], ...]
        self.guilds: dict[str, list] = defaultdict(list)     # guild -> [[t, treasury, members, active, gear], ...]
        self.fights: list[dict] = []
        self.quests: dict[str, list] = defaultdict(list)
        self.trader: list[dict] = []
        self.first = self.last = None
        self.runs = 0
        board: list[str] = []
        guild_now: dict[str, dict] = {}
        for rec in records:
            t = rec["t"]
            self.first = self.first or t
            self.last, self.runs = t, self.runs + 1
            for login, p in rec.get("players", {}).items():
                for series, key in ((self.gear, "gear"), (self.donated, "donated"), (self.guild, "guild")):
                    if key in p and (p[key] is not None or key == "guild"):  # a record only has changed fields
                        put(series[login], t, p[key])
            for login, d in rec.get("details", {}).items():
                self.details[login].append([t, d])
            if "gear" in rec.get("boards", {}):
                new = [login for login, _ in rec["boards"]["gear"]]
                for login in set(board) - set(new):
                    put(self.rank[login], t, None)
                for i, login in enumerate(new):
                    put(self.rank[login], t, i + 1)
                board = new
            for g, v in rec.get("guilds", {}).items():
                full = guild_now[g] = {**guild_now.get(g, {}), **v}
                self.guilds[g].append([t, *(full.get(k) for k in ("treasury", "members", "active", "gear"))])
            self.fights += rec.get("fights", [])
            for login, qs in rec.get("quests", {}).items():
                self.quests[login] += qs
            if tr := rec.get("trader"):
                if tr.get("channel") and (not self.trader or self.trader[-1]["channel"] != tr["channel"]
                                          or t - self.trader[-1]["t"] > 1800):
                    self.trader.append({"t": t, "channel": tr["channel"]})


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


QUEST_SILVER = re.compile(r"erhält (?:(\d+) Gold)?\s*(?:(\d+) Silber)?")


def quest_silver(line: str) -> int:
    m = QUEST_SILVER.search(line or "")
    return int(m.group(1) or 0) * 100 + int(m.group(2) or 0) if m and (m.group(1) or m.group(2)) else 0


def fight_groups(fights: list[dict], now: float, days: int = 30) -> list[dict]:
    """Win rate per fight type: bosses by name and level, the rest by kind and difficulty."""
    groups: dict[tuple, list] = defaultdict(list)
    for f in fights:
        ended = iso_ts(f.get("endedAt"))
        if ended and ended < now - days * DAY:
            continue
        key = ("BOSS", f.get("name"), f.get("bossLevel")) if f.get("kind") == "BOSS" \
            else (f.get("kind"), None, f.get("difficulty"))
        groups[key].append(f)
    out = [{"kind": k[0], "name": k[1], "level": k[2], "n": len(fs),
            "wins": sum(1 for f in fs if f.get("outcome") == "VICTORY"),
            "fighters": round(statistics.mean(f.get("fighters") or 0 for f in fs))} for k, fs in groups.items()]
    return sorted(out, key=lambda g: (g["kind"], g["name"] or "", g["level"] or 0))


def iso_ts(s: str | None) -> float | None:
    if not s:
        return None
    from datetime import datetime
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def build(data: Path, out: Path, now: float | None = None) -> dict:
    h = History(replay(data / "days"))
    state = json.loads((data / "state.json").read_text("utf-8"))
    now = now or h.last or time.time()
    players, details, guilds = state["players"], state["details"], state["guilds"]
    gear = {login: p["gear"] for login, p in players.items() if p.get("gear") is not None}
    order = sorted(gear.values(), reverse=True)

    def rank(g):  # ties share a rank
        return bisect.bisect_left([-x for x in order], -g) + 1

    paces = {login: pace(h.gear[login], now) for login in gear}
    day = {login: change(h.gear[login], now, DAY) for login in gear}
    week = {login: change(h.gear[login], now, 7 * DAY) for login in gear}
    board_gear = dict(state["boards"].get("gear", []))
    board = list(board_gear)
    ranks_24h = {login: value_at(h.rank[login], now - DAY) for login in board}
    top100_gear = board_gear[board[-1]] if len(board) >= 100 else None
    tail_paces = [paces[x] for x in board[89:100] if paces.get(x) is not None]
    top100_pace = statistics.median(tail_paces) if tail_paces else None

    def row(login):
        p = players[login]
        return {"login": login, "name": p.get("name") or login, "gear": p.get("gear"), "guild": p.get("guild"),
                "day": day.get(login), "week": week.get(login), "pace": rounded(paces.get(login))}

    def risers(changes):
        best = sorted((login for login in changes if changes[login]), key=lambda x: -changes[x])[:25]
        return [row(login) for login in best]

    board_rows = []
    for i, login in enumerate(board):
        prev = ranks_24h.get(login)
        board_rows.append({**row(login), "rank": i + 1, "rank_change": None if prev is None else prev - (i + 1),
                           "board_gear": board_gear[login],
                           **{k: details.get(login, {}).get(k) for k in ("atk", "def", "sup")}})

    def value_board(name: str, key: str):
        """A ranking by one value: rank, the board's own value and its change in 24 hours."""
        return [{**row(login), "rank": i + 1, "value": v,
                 "value_day": change([[t, d[key]] for t, d in h.details[login] if d.get(key)], now, DAY)}
                for i, (login, v) in enumerate(state["boards"].get(name, []))]

    quest_rows = value_board("quests", "quests")
    silver_rows = value_board("gold", "silver")
    achievement_rows = value_board("errungenschaften", "ach")

    guild_members: dict[str, list[str]] = defaultdict(list)
    for login, p in players.items():
        if p.get("guild"):
            guild_members[p["guild"]].append(login)
    guild_rows = []
    for g, info in guilds.items():
        members = guild_members.get(g, [])
        guild_rows.append({"login": g, **info, "day": sum(day.get(m) or 0 for m in members),
                           "donated": sum(players[m].get("donated") or 0 for m in members),
                           "top": [row(m) for m in sorted(members, key=lambda m: -(players[m].get("gear") or 0))[:10]],
                           "donors": [{**row(m), "donated": players[m].get("donated")}
                                      for m in sorted(members, key=lambda m: -(players[m].get("donated") or 0))[:10]],
                           "series": h.guilds.get(g, [])})

    summary = {"generated": int(now), "since": h.first, "runs": h.runs, "players": len(gear),
               "active": sum(1 for p in players.values() if p.get("active")),
               "board": board_rows, "quests": quest_rows, "silver": silver_rows,
               "achievements": achievement_rows,
               "risers": {"day": risers(day), "week": risers(week)},
               "top100": {"gear": top100_gear, "pace": rounded(top100_pace)},
               "guilds": sorted(guild_rows, key=lambda g: -(g.get("gear") or 0)),
               "fights": {"groups": fight_groups(h.fights, now), "recent": h.fights[-50:][::-1],
                          "total": len(h.fights)},
               "trader": h.trader[-50:][::-1], "channels": state.get("channels", {})}

    target = out / "data"
    if target.exists():
        shutil.rmtree(target)
    (target / "p").mkdir(parents=True)
    write(target / "summary.json", summary)
    write(target / "players.json", sorted(([login, p.get("name") or login, p.get("gear"), p.get("guild")]
                                           for login, p in players.items() if p.get("gear") is not None),
                                          key=lambda r: -r[2]))
    with_split = [x for x in gear if all(details.get(x, {}).get(k) is not None for k in ("atk", "def", "sup"))]
    for login in gear:
        write(target / "p" / f"{login}.json", player_page(login, h, state, now, rank, paces, with_split,
                                                          top100_gear, top100_pace, guild_members))
    return summary


def player_page(login, h, state, now, rank, paces, with_split, top100_gear, top100_pace, guild_members) -> dict:
    players, details = state["players"], state["details"]
    p = players[login]
    g = p["gear"]
    my_pace = paces.get(login)
    higher = sorted({x["gear"] for x in players.values() if x.get("gear") is not None and x["gear"] > g})
    next_gap = higher[0] - g + 1 if higher else None
    on_board = h.rank[login][-1][1] if h.rank.get(login) else None
    forecast = {"rank": on_board or rank(g), "exact": on_board is not None, "next_gap": next_gap,
                "next_days": rounded(next_gap / my_pace, 1) if next_gap and my_pace and my_pace > 0 else None,
                "top100_gap": None, "top100_days": None}
    if top100_gear is not None and g <= top100_gear:
        gap = top100_gear - g + 1
        forecast["top100_gap"] = gap
        edge = my_pace - (top100_pace or 0) if my_pace is not None else None
        forecast["top100_days"] = rounded(gap / edge, 1) if edge and edge > 0 else None

    # Peers: players with a known split and a similar gear score (the nearest ones, at least PEERS_MIN).
    others = sorted((x for x in with_split if x != login), key=lambda x: abs(players[x]["gear"] - g))
    close = [x for x in others if abs(players[x]["gear"] - g) <= max(10, g * 0.05)]
    peers = close if len(close) >= PEERS_MIN else others[:PEERS_MIN]
    split = None
    if peers:
        split = {k: round(statistics.mean(details[x][k] for x in peers), 1) for k in ("atk", "def", "sup")}
        split["n"], split["gear"] = len(peers), round(statistics.mean(players[x]["gear"] for x in peers))
        split["pace"] = rounded(statistics.median(known)) if (known := [paces[x] for x in peers
                                                                          if paces.get(x) is not None]) else None

    guild = None
    if p.get("guild"):
        members = sorted(guild_members[p["guild"]], key=lambda m: -(players[m].get("donated") or 0))
        pos = members.index(login)
        above = players[members[pos - 1]].get("donated") or 0 if pos else None
        by_gear = sorted(guild_members[p["guild"]], key=lambda m: -(players[m].get("gear") or 0))
        info = state["guilds"].get(p["guild"], {})
        guild = {"login": p["guild"], "name": info.get("name"), "members": len(members),
                 "donated": p.get("donated"), "donation_rank": pos + 1,
                 "donation_gap": above - (p.get("donated") or 0) + 1 if above is not None else None,
                 "gear_rank": by_gear.index(login) + 1,
                 "gear_share": rounded(100 * g / info["gear"], 3) if info.get("gear") else None}

    watch = state.get("watch", {}).get(login)
    quests = h.quests.get(login, [])
    return {"login": login, "name": p.get("name") or login, "gear": g, "guild": guild, "active": p.get("active"),
            "pace": rounded(my_pace), "day": change(h.gear[login], now, DAY),
            "week": change(h.gear[login], now, 7 * DAY), "forecast": forecast,
            "board_rank": on_board,
            "split": {k: details.get(login, {}).get(k) for k in ("atk", "def", "sup", "silver", "quests")},
            "peers": split,
            "series": {"gear": h.gear[login], "donated": h.donated.get(login, []), "rank": h.rank.get(login, []),
                       "silver": [[t, d.get("silver")] for t, d in h.details.get(login, [])
                                  if d.get("silver") is not None]},
            "watch": None if not watch else {**watch, "quests": [{**q, "silver": quest_silver(q.get("line"))}
                                                                 for q in quests[-100:][::-1]]}}


def write(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), "utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, default=Path("_site"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(__file__).with_name("site") / "index.html", args.out / "index.html")
    summary = build(args.data, args.out)
    print(f"{summary['players']} Spieler, {summary['runs']} Läufe, {summary['fights']['total']} Kämpfe")


if __name__ == "__main__":
    main()
