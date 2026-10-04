"""Fight statistics: sums over the archive's fights, never anything per player.

`fights` are the fight lines of the history (id, channel, kind, name, difficulty, bossLevel, outcome, fighters,
endedAt), `extra` the digests collect.py stored per fight id (who fell, roles, damage; from the live view also the
average gear and power and the recommendation). Digests exist only for fights collected since 0.9.0.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

DAY = 86400
BERLIN = ZoneInfo("Europe/Berlin")
ROLE_NAMES = ("TANK", "FIGHTER", "SUPPORT")
MARGINS = ((0, 0.8), (0.8, 1.0), (1.0, 1.2), (1.2, 1e9))  # average power / recommendation


def iso_ts(s: str | None) -> float | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def fight_key(f: dict) -> tuple:
    """Bosses by name and level, the rest by kind and difficulty."""
    if f.get("kind") == "BOSS":
        return ("BOSS", f.get("name"), f.get("bossLevel"))
    return (f.get("kind"), None, f.get("difficulty"))


def pct(part, whole, digits=1):
    return round(100 * part / whole, digits) if whole else None


def mean(xs, digits=0):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), digits or None) if xs else None


def digest_totals(digests: list[dict]) -> dict:
    """Pooled numbers over fights that have a detail digest: every fighter counts once."""
    people = sum(sum(d["roles"]) for d in digests)
    dead = sum(sum(d["dead"]) for d in digests)
    return {"people": people, "dead": dead, "death": pct(dead, people),
            "dmg": mean([d["dmg"] / sum(d["roles"]) for d in digests if d.get("dmg") is not None and sum(d["roles"])]),
            "taken": mean([d["taken"] / sum(d["roles"]) for d in digests
                           if d.get("taken") is not None and sum(d["roles"])]),
            "heal": mean([d["heal"] / sum(d["roles"]) for d in digests
                          if d.get("heal") is not None and sum(d["roles"])]),
            "rounds": mean([d["round"] for d in digests if d.get("round")], 1),
            "pay_alive": mean([d["pay"][0] for d in digests if d.get("pay")]),
            "pay_dead": mean([d["pay"][1] for d in digests if d.get("pay")])}


def fallen(d: dict | None) -> dict:
    """Who fell in one fight, from its digest (nothing when there is none)."""
    if not d or "roles" not in d or not sum(d["roles"]):
        return {}
    return {"dead": sum(d["dead"]), "death": pct(sum(d["dead"]), sum(d["roles"]))}


def summarize(fs: list[dict], extra: dict[int, dict]) -> dict:
    """One row for a set of fights: counts, win rate, and the digest numbers where there are any."""
    digests = [extra[f["id"]] for f in fs if "roles" in extra.get(f["id"], {})]
    wins = [f for f in fs if f.get("outcome") == "VICTORY"]
    row = {"n": len(fs), "wins": len(wins), "fighters": mean([f.get("fighters") or 0 for f in fs]),
           "detail": len(digests)}
    if digests:
        row.update(digest_totals(digests))
        for name, group in (("death_win", wins), ("death_loss", [f for f in fs if f not in wins])):
            ds = [extra[f["id"]] for f in group if "roles" in extra.get(f["id"], {})]
            row[name] = digest_totals(ds)["death"] if ds else None
    return row


def fight_stats(fights: list[dict], extra: dict[int, dict], now: float, days: int = 30) -> dict:
    window = [f for f in fights if not (t := iso_ts(f.get("endedAt"))) or t >= now - days * DAY]
    detailed = [f for f in window if "roles" in extra.get(f["id"], {})]

    kinds: dict[str, list] = defaultdict(list)
    types: dict[tuple, list] = defaultdict(list)
    hours: dict[int, list] = defaultdict(list)
    channels: dict[str, list] = defaultdict(list)
    day_rows: dict[str, list] = defaultdict(list)
    for f in window:
        kinds[f.get("kind")].append(f)
        types[fight_key(f)].append(f)
        channels[f.get("channel")].append(f)
        if t := iso_ts(f.get("endedAt")):
            local = datetime.fromtimestamp(t, BERLIN)
            hours[local.hour].append(f)
            day_rows[f"{local:%Y-%m-%d}"].append(f)

    type_rows = []
    for k, fs in types.items():
        row = {"kind": k[0], "name": k[1], "level": k[2], **summarize(fs, extra)}
        defeats = [extra[f["id"]] for f in fs if f.get("outcome") != "VICTORY" and extra.get(f["id"], {}).get("maxhp")]
        row["boss_left"] = mean([100 * d["hp"] / d["maxhp"] for d in defeats if d.get("hp") is not None], 1) \
            if defeats else None
        row["maxhp"] = mean([extra[f["id"]].get("maxhp") for f in fs if extra.get(f["id"], {}).get("maxhp")])
        power = [(extra[f["id"]], f) for f in fs if extra.get(f["id"], {}).get("power")]
        row["power"] = mean([d["power"] for d, _ in power])
        row["power_win"] = mean([d["power"] for d, f in power if f.get("outcome") == "VICTORY"])
        row["power_loss"] = mean([d["power"] for d, f in power if f.get("outcome") != "VICTORY"])
        row["rec"] = mean([d["rec"] for d, _ in power if d.get("rec")])
        type_rows.append(row)
    type_rows.sort(key=lambda r: (-(r["wins"] / r["n"]), -r["n"], r["kind"], r["name"] or "", r["level"] or 0))

    # A lost boss fight takes everyone down, so the role split only counts won fights.
    won = [f for f in detailed if f.get("outcome") == "VICTORY"]
    role_people = [sum(extra[f["id"]]["roles"][i] for f in won) for i in range(3)]
    role_dead = [sum(extra[f["id"]]["dead"][i] for f in won) for i in range(3)]
    roles = [{"role": ROLE_NAMES[i], "share": pct(role_people[i], sum(role_people)),
              "death": pct(role_dead[i], role_people[i])} for i in range(3)] if won else []

    with_power = [(extra[f["id"]], f) for f in window if extra.get(f["id"], {}).get("power")]
    margins = []
    for lo, hi in MARGINS:
        sel = [f for d, f in with_power if d.get("rec") and lo <= d["power"] / d["rec"] < hi]
        margins.append({"from": lo, "to": hi if hi < 1e9 else None, **summarize(sel, extra)} if sel
                        else {"from": lo, "to": hi if hi < 1e9 else None, "n": 0})
    return {
        "days": days, "detail": len(detailed), "fights": len(window),
        "since_detail": min((iso_ts(f.get("endedAt")) or 0 for f in detailed), default=None),
        "total": summarize(window, extra),
        "kinds": sorted(({"kind": k, **summarize(fs, extra)} for k, fs in kinds.items()), key=lambda r: -r["n"]),
        "types": type_rows, "roles": roles,
        "hours": [{"hour": h, **summarize(hours[h], extra)} if hours.get(h) else {"hour": h, "n": 0}
                  for h in range(24)],
        "channels": sorted(({"channel": c, **summarize(fs, extra)} for c, fs in channels.items()),
                           key=lambda r: (-r["n"], r["channel"] or "")),
        "daily": [{"day": d, **summarize(fs, extra)} for d, fs in sorted(day_rows.items())],
        "power": {"n": len(with_power), "avg": mean([d["power"] for d, _ in with_power]),
                  "avg_gear": mean([d["gear"] for d, _ in with_power]),
                  "rec": mean([d["rec"] for d, _ in with_power if d.get("rec")]),
                  "margins": margins,
                  "recent": [{"id": f["id"], "kind": f.get("kind"), "name": f.get("name"), "outcome": f.get("outcome"),
                              "power": d["power"], "gear": d.get("gear"), "rec": d.get("rec") or None,
                              "enraged": d.get("enraged"), "secs": d.get("secs"), **fallen(d)}
                             for d, f in sorted(with_power, key=lambda x: -x[1]["id"])[:30]]},
    }
