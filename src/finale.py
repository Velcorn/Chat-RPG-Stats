"""The season's story for the review page: who held the top, who got there first, the records.

Everything is read from what the collector already keeps (`build.History`): the first place and its score at every
run, the gear scores per player and the donation and Kampfkraft values of the state. Nothing new is requested.
"""
from __future__ import annotations

from collections import defaultdict

TOP_N = 5


def _name(players: dict, login: str) -> str:
    return (players.get(login) or {}).get("name") or login


def top_story(h, players: dict, since: float = 0) -> dict | None:
    """The highest gear score over time and who held it. Players on the same score are ordered by silver, so only the
    first of the board holds the top (a shared score doesn't share it); every run of the collector counts, the time
    between two changes of the first place goes to its holder.
    `holders`: [login, name, hours at the top, longest stretch in hours], most hours first; `first`: who reached the
    final top score first; `series`: [[t, top score], ...] (only changes)."""
    if not h.leader or h.last is None or h.last <= since:
        return None
    hours: dict[str, float] = defaultdict(float)
    longest: dict[str, float] = defaultdict(float)
    for (t, login), nxt in zip(h.leader, [*h.leader[1:], [h.last, None]], strict=True):
        spent = (nxt[0] - max(t, since)) / 3600
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
    return {"score": final, "series": series,
            "now": sum(1 for _, score in h.board_last if score == final),
            "first": {"login": first[1], "name": _name(players, first[1]), "t": first[0]} if first else None,
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
