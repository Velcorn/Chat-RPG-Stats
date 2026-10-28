"""The season's story for the review page: who held the top, who got there first, the records.

Everything is read from what the collector already keeps (`build.History`): the first place and its score at every
run, the gear scores per player and the donation and Kampfkraft values of the state. Nothing new is requested.
"""
from __future__ import annotations

import statistics
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime
from itertools import pairwise
from zoneinfo import ZoneInfo

TOP_N = 5
ALT_MAX = 680  # the other highest score: what a build with a two-hander tops out at
BERLIN = ZoneInfo("Europe/Berlin")


def open_hours(window: list[list], a: float, b: float) -> float:
    """Hours between a and b (timestamps) inside the game's play window, which the Sperrstunde closes (Berlin time;
    `window` is [[t, from, to], ...] at every change, `to` may come as 27 for 3 o'clock). No window known: all of it."""
    if not window:
        return max(0.0, b - a) / 3600
    starts = [w[0] for w in window]
    total, t = 0.0, a
    while t < b:
        nxt = min(b, (t // 3600 + 1) * 3600)  # the next full hour (Berlin zones are whole hours from UTC)
        _, start, end = window[max(0, bisect_right(starts, t) - 1)]
        start, end, hour = start % 24, end % 24, datetime.fromtimestamp(t, BERLIN).hour
        if start == end or (start <= hour < end if start < end else hour >= start or hour < end):
            total += nxt - t
        t = nxt
    return total / 3600


def _name(players: dict, login: str) -> str:
    return (players.get(login) or {}).get("name") or login


def top_story(h, players: dict, since: float = 0) -> dict | None:
    """The highest gear score over time and who held it. Players on the same score are ordered by silver, so only the
    first of the board holds the top (a shared score doesn't share it); every run of the collector counts, the time
    between two changes of the first place goes to its holder, without the hours of the Sperrstunde.
    `holders`: [login, name, hours at the top, longest stretch in hours], most hours first; `first`: who reached the
    final top score first, `first_alt` who reached `alt` (the other highest score, a two-hander's) first, `now` counts
    both; `series`: [[t, top score], ...] (only changes)."""
    if not h.leader or h.last is None or h.last <= since:
        return None
    hours: dict[str, float] = defaultdict(float)
    longest: dict[str, float] = defaultdict(float)
    for (t, login), nxt in zip(h.leader, [*h.leader[1:], [h.last, None]], strict=True):
        spent = open_hours(h.window, max(t, since), nxt[0])
        if spent > 0:
            hours[login] += spent
            longest[login] = max(longest[login], spent)
    series = [p for p in h.top_score if p[0] >= since]
    before = [p for p in h.top_score if p[0] < since]
    if before and (not series or series[0][0] > since):
        series.insert(0, [since, before[-1][1]])
    if not series:
        return None
    final = series[-1][1]
    first = min(((t, login) for login, s in h.gs.items() for t, v in s if t >= since and v >= final), default=None)
    alt = min(((t, login) for login, s in h.gs.items() for t, v in s if t >= since and v >= ALT_MAX), default=None)
    alt = alt if ALT_MAX < final else None
    return {"score": final, "series": series, "alt": ALT_MAX if ALT_MAX < final else None,
            "now": sum(1 for _, score in h.board_last if score in (final, ALT_MAX)),
            "first": {"login": first[1], "name": _name(players, first[1]), "t": first[0]} if first else None,
            "first_alt": {"login": alt[1], "name": _name(players, alt[1]), "t": alt[0]} if alt else None,
            "holders": [[login, _name(players, login), round(hours[login], 2), round(longest[login], 2)]
                        for login in sorted(hours, key=lambda x: -hours[x])[:TOP_N]],
            "ever": len(hours)}


def records(h, players: dict) -> dict:
    """Records of the season as the state has them: the biggest donors and the highest Kampfkraft."""
    def best(key):
        rows = [(login, p[key]) for login, p in players.items() if p.get(key)]
        return [[login, _name(players, login), v, players[login].get("guild")]
                for login, v in sorted(rows, key=lambda r: -r[1])[:TOP_N]]
    return {"donors": best("donated"), "power": best("gear")}


def finale(h, players: dict, since: float = 0) -> dict:
    """`since`: the board showed Kampfkraft before it, so those frames and scores are left out."""
    return {"top": top_story(h, players, since), "records": records(h, players)}


DAY = 86400
MIN_BUILDS = 30  # tracked players needed for a build average to mean anything
SERIES_POINTS = 90


def _day(t: float) -> int:
    """Midnight (Berlin) of the day t falls on, as a timestamp."""
    d = datetime.fromtimestamp(t, BERLIN)
    return int(d.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())


def _thin(series: list, n: int = SERIES_POINTS) -> list:
    step = max(1, len(series) // n)
    return [*series[::step][:n - 1], series[-1]]


def overtakes(h) -> dict | None:
    """Changes of the first place: how many, per day, how many at the same score (silver decided) and the longest
    stretch one player held it."""
    if len(h.leader) < 2:
        return None
    by_day: dict[int, int] = defaultdict(int)
    same = 0
    for (_, before), (t, after) in pairwise(h.leader):
        by_day[_day(t)] += 1
        scores = []
        for login in (before, after):
            series = h.gs.get(login, [])
            i = bisect_right([x[0] for x in series], t) - 1
            scores.append(series[i][1] if i >= 0 else None)
        same += scores[0] is not None and scores[0] == scores[1]
    longest = max(((nxt[0] - cur[0]) / 3600, cur[1]) for cur, nxt in pairwise(h.leader))
    return {"changes": len(h.leader) - 1, "silver": same, "per_day": sorted(by_day.items()),
            "longest": {"hours": round(longest[0], 1), "login": longest[1]}}


def activity(h) -> list[list[int]]:
    """Finished fights by weekday (Monday first) and hour of the day, Berlin time."""
    grid = [[0] * 24 for _ in range(7)]
    for f in h.fights:
        t = _iso(f.get("endedAt"))
        if t:
            d = datetime.fromtimestamp(t, BERLIN)
            grid[d.weekday()][d.hour] += 1
    return grid


def _iso(text: str | None) -> float | None:
    if not text:
        return None
    return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()


def growth(h) -> dict:
    """The highest gear score gained per day, and the days the game's rules changed (`marks`: [day, [rule, ...]])."""
    last: dict[int, int] = {}
    for t, score in h.top_score:
        last[_day(t)] = score
    days = sorted(last)
    gains = [[d, last[d] - last[prev]] for prev, d in pairwise(days)]
    marks: dict[int, list[str]] = defaultdict(list)
    for t, rule, *_ in h.rules_log:
        if rule not in marks[_day(t)]:
            marks[_day(t)].append(rule)
    return {"gains": gains, "marks": sorted(marks.items())}


def builds(h) -> list[list]:
    """Average share of attack, defense and support among the players whose split is known, per three days:
    [day, atk, def, sup, players]."""
    per: dict[int, dict[str, tuple]] = defaultdict(dict)
    for login, rows in h.details.items():
        for t, d in rows:
            split = (d.get("atk"), d.get("def"), d.get("sup"))
            if None not in split and sum(split) > 0:
                per[int(t // (3 * DAY))][login] = split
    out = []
    for k in sorted(per):
        v = list(per[k].values())
        if len(v) >= MIN_BUILDS:
            out.append([k * 3 * DAY, *(round(statistics.fmean(x[i] / sum(x) for x in v), 4) for i in range(3)), len(v)])
    return out


def guild_gear(h, guilds: dict) -> list[dict]:
    """Average gear score of the active members for every guild with at least ten of them: [{login, series}]."""
    out = []
    for login, g in guilds.items():
        rows = [[r[0], round(r[4] / r[3], 1)] for r in h.guilds.get(login, []) if r[3] and r[4]]
        if g.get("active", 0) >= 10 and rows:
            out.append({"login": login, "name": g.get("name") or login, "series": _thin(rows)})
    return out


def abspann(h, guilds: dict) -> dict:
    """Everything the credits page draws that no other summary field already holds."""
    return {"overtakes": overtakes(h), "activity": activity(h), "growth": growth(h), "builds": builds(h),
            "guilds": guild_gear(h, guilds)}
