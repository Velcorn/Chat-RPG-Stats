"""Time lapse of the gear scores: every six hours the score per percentile and a histogram, for all and per guild.

A player counts from the first moment the history knows their score; the daily profile sweep reads the guild members
in slices, so early frames hold fewer players. Frames start where at least COVERAGE of today's players are known, the
histograms are shares (not counts) so the growing coverage doesn't show as growing bars.
"""
from __future__ import annotations

import bisect

STEP = 6 * 3600
BIN = 20
COVERAGE = 0.8
MIN_ACTIVE = 10  # guilds below this have no line (like the tabs on the start page)


def _at(series: list, times: list, t: float):
    i = bisect.bisect_right(times, t)
    return series[i - 1][1] if i else None


def timelapse(h, players: dict, border_series: list) -> dict | None:
    """The data for the Zeitraffer page, or None with fewer than two frames. `h` is a build.History."""
    live = [login for login, p in players.items() if p.get("active") and h.gs.get(login)]
    if not live or not h.last:
        return None
    gs_t = {login: [t for t, _ in h.gs[login]] for login in live}
    gu_t = {login: [t for t, _ in h.guild.get(login, [])] for login in live}

    def known(t: float) -> dict[str, tuple[int, str | None]]:
        out = {}
        for login in live:
            v = _at(h.gs[login], gs_t[login], t)
            if v is not None:
                out[login] = (v, _at(h.guild.get(login, []), gu_t[login], t))
        return out

    last = known(h.last)
    times = [h.last]
    t = int(h.last) // STEP * STEP
    while t > h.first and len(known(t)) >= COVERAGE * len(last):
        if h.last - t >= STEP / 2:
            times.append(t)
        t -= STEP
    times.reverse()
    if len(times) < 2:
        return None
    guilds = sorted({g for _, g in last.values() if g}, key=lambda g: (-sum(1 for _, x in last.values() if x == g), g))
    guilds = [g for g in guilds if sum(1 for _, x in last.values() if x == g) >= MIN_ACTIVE]
    frames = [known(t) for t in times]
    every = [v for f in frames for v, _ in f.values()]
    lo = min(every) // BIN * BIN
    bins = (max(every) - lo) // BIN + 1
    groups = [{"login": None, "name": "Alle"}, *({"login": g, "name": g} for g in guilds)]
    for grp in groups:
        grp.update(mean=[], pct=[], hist=[])
        for f in frames:
            vals = sorted(v for v, g in f.values() if grp["login"] is None or g == grp["login"])
            n = len(vals)
            grp["mean"].append(round(sum(vals) / n, 1) if n else None)
            grp["pct"].append([vals[round(p / 100 * (n - 1))] for p in range(101)] if n else None)
            counts = [0] * bins
            for v in vals:
                counts[(v - lo) // BIN] += 1
            grp["hist"].append([round(100 * c / n, 2) for c in counts] if n else None)
    return {"frames": [round(t) for t in times], "bin": BIN, "lo": lo, "groups": groups,
            "border": [_at(border_series, [x for x, _ in border_series], t) for t in times]}


def top_lapse(h, players: dict) -> dict | None:
    """The gear board (top 100) at every grid time of `h.board_at`: {"names", "frames", "rows"}, rows per frame
    [[player index, score], ...] in board order. None with fewer than two frames."""
    times = sorted(h.board_at)
    if len(times) < 2:
        return None
    index: dict[str, int] = {}
    names: list[str] = []
    rows = []
    for t in times:
        row = []
        for login, score in h.board_at[t]:
            if login not in index:
                index[login] = len(names)
                names.append((players.get(login) or {}).get("name") or login)
            row.append([index[login], score])
        rows.append(row)
    return {"names": names, "logins": list(index), "frames": times, "rows": rows}
