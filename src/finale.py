"""The season's story for the review page: who held the top, who got there first, the records.

Everything is read from what the collector already keeps (`build.History`): the top-100 board at every grid time, the
gear scores per player and the donation and Kampfkraft values of the state. Nothing new is requested.
"""
from __future__ import annotations

from collections import defaultdict

TOP_N = 5


def _name(players: dict, login: str) -> str:
    return (players.get(login) or {}).get("name") or login


def top_story(h, players: dict, grid: int, since: float = 0) -> dict | None:
    """The highest gear score over time and who held it. Players on the same score share the top (the game orders
    them by something else), so a place at the top means "had the highest score", alone or not.
    `holders`: [login, name, hours at the top, longest stretch in hours], most hours first; `first`: who reached the
    final top score first; `series`: [[t, top score], ...] (only changes)."""
    times = sorted(t for t in h.board_at if t >= since)
    if not times:
        return None
    series: list[list] = []
    hours: dict[str, float] = defaultdict(float)
    longest: dict[str, float] = defaultdict(float)
    run: dict[str, float] = {}
    for t in times:
        rows = h.board_at[t]
        top = rows[0][1]
        if not series or series[-1][1] != top:
            series.append([t, top])
        holders = {login for login, score in rows if score == top}
        for login in holders:
            hours[login] += grid / 3600
            run[login] = run.get(login, 0) + grid / 3600
            longest[login] = max(longest[login], run[login])
        for login in set(run) - holders:
            del run[login]
    final = series[-1][1]
    first = min(((t, login) for login, s in h.gs.items() for t, v in s if t >= since and v >= final), default=None)
    return {"score": final, "series": series,
            "now": sum(1 for _, score in h.board_at[times[-1]] if score == final),
            "first": {"login": first[1], "name": _name(players, first[1]), "t": first[0]} if first else None,
            "holders": [[login, _name(players, login), round(hours[login], 1), round(longest[login], 1)]
                        for login in sorted(hours, key=lambda x: -hours[x])[:TOP_N]],
            "ever": len(hours)}


def records(h, players: dict, since: float = 0) -> dict:
    """Records of the season: the biggest gear gain since the first measurement, the biggest donors and the highest
    Kampfkraft (the latter two as the state has them)."""
    growth = []
    for login, series in h.gs.items():
        s = [p for p in series if p[0] >= since and p[1] > 0]  # a 0 is a player not read yet
        if len(s) >= 2 and s[-1][1] > s[0][1]:
            growth.append([login, _name(players, login), s[-1][1] - s[0][1], s[0][1], s[-1][1]])
    growth.sort(key=lambda r: -r[2])

    def best(key):
        rows = [(login, p[key]) for login, p in players.items() if p.get(key)]
        return [[login, _name(players, login), v, players[login].get("guild")]
                for login, v in sorted(rows, key=lambda r: -r[1])[:TOP_N]]
    return {"growth": growth[:TOP_N], "donors": best("donated"), "power": best("gear")}


def finale(h, players: dict, grid: int, since: float = 0) -> dict:
    """`since`: the board showed Kampfkraft before it, so those frames and scores are left out."""
    return {"top": top_story(h, players, grid, since), "records": records(h, players, since)}
