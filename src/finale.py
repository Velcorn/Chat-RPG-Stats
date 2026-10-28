"""The season's story for the review page: who held the top, who got there first, the records.

Everything is read from what the collector already keeps (`build.History`): the first place and its score at every
run, the gear scores per player and the donation and Kampfkraft values of the state. Nothing new is requested.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from datetime import datetime
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
