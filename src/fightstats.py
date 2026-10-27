"""Fight statistics: sums over the archive's fights, never anything per player.

`fights` are the fight lines of the history (id, channel, kind, name, difficulty, bossLevel, outcome, fighters,
endedAt), `extra` the digests collect.py stored per fight id (who fell, roles, damage; from the live view also the
average gear and power and the recommendation). Digests exist only for fights collected since 0.9.0.
"""
from __future__ import annotations

import csv
import io
import math
import statistics
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

DAY = 86400
BERLIN = ZoneInfo("Europe/Berlin")
ROLE_NAMES = ("TANK", "FIGHTER", "SUPPORT")
UPDATE = 1791059580  # 2026-10-03 20:33 UTC: the story update (adventures with chat votes, no rounds)
MARGINS = ((0, 0.8), (0.8, 1.0), (1.0, 1.2), (1.2, 1e9))  # average power / recommendation


def iso_ts(s: str | None) -> float | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def fight_key(f: dict) -> tuple:
    """Bosses by name and level, raids by name and difficulty, adventures by name (their difficulty is always 3)."""
    if f.get("kind") == "BOSS":
        return ("BOSS", f.get("name"), f.get("bossLevel"))
    return (f.get("kind"), f.get("name"), f.get("difficulty") if f.get("kind") == "RAID" else None)


def pct(part, whole, digits=1):
    return round(100 * part / whole, digits) if whole else None


def mean(xs, digits=0):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), digits or None) if xs else None


def digest_totals(digests: list[dict]) -> dict:
    """Pooled numbers over fights that have a detail digest: every fighter counts once."""
    people = sum(sum(d["roles"]) for d in digests)
    dead = sum(sum(d["dead"]) for d in digests)
    # Adventures without a fight (the chat's story ends before one) have an all-zero tally: they would only pull
    # the averages down.
    fought = [d for d in digests if d.get("dmg")]

    def per_head(key):
        return mean([d[key] / sum(d["roles"]) for d in fought if d.get(key) is not None and sum(d["roles"])])
    return {"people": people, "dead": dead, "death": pct(dead, people),
            "dmg": per_head("dmg"), "taken": per_head("taken"), "heal": per_head("heal"), "boost": per_head("boost"),
            "rounds": mean([d["round"] for d in digests if d.get("round") and (d.get("rounds") or 0) > 1], 1),
            "pay_alive": mean([d["pay"][0] for d in digests if d.get("pay")]),
            "pay_dead": mean([d["pay"][1] for d in digests if d.get("pay")])}


def fallen(d: dict | None) -> dict:
    """Who fell in one fight, from its digest (nothing when there is none)."""
    if not d or "roles" not in d or not sum(d["roles"]):
        return {}
    return {"dead": sum(d["dead"]), "death": pct(sum(d["dead"]), sum(d["roles"]))}


def whose(d: dict | None) -> dict:
    """The guild a fight was about, who summoned the boss and what the treasury lost (from its digest)."""
    return {k: d[k] for k in ("gn", "by", "gc") if d and d.get(k) is not None}


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


GG_MIN = 10  # fights with the game's group gear (potions, mead, talents counted) before it replaces the Kampfkraft


def strength_basis(ds: list[dict]) -> str:
    """What a group's strength is measured by: the game's group gear (`gg`, in the unit of the recommendation, with
    talents, potions and mead) once at least GG_MIN fights have it, else the plain Kampfkraft (gear plus talents)."""
    return "gg" if sum(1 for d in ds if d.get("gg")) >= GG_MIN else "power"


def current(f: dict, d: dict, boss_rec: dict | None) -> bool:
    """A boss fight counts for the power numbers only if its recommendation is the boss's recommendation now: a
    boss that was made stronger (its recommendation changed) is not the boss of the older fights. Everything else
    (adventures, raids, bosses the compendium doesn't know) counts."""
    now = (boss_rec or {}).get(f.get("name"))
    return not (f.get("kind") == "BOSS" and now and d.get("rec") != now)


def fight_stats(fights: list[dict], extra: dict[int, dict], now: float, days: int = 30,
                lo: float | None = None, hi: float | None = None, boss_rec: dict | None = None) -> dict:
    """The numbers for the last `days` days; `lo`/`hi` cut a game version out of that (fights without a time
    belong to no version); `boss_rec` (name -> recommendation now) keeps the power numbers to bosses as they are."""
    window = [f for f in fights if not (t := iso_ts(f.get("endedAt"))) or t >= now - days * DAY]
    if lo is not None or hi is not None:
        window = [f for f in window if (t := iso_ts(f.get("endedAt"))) and t >= (lo or 0) and t < (hi or 1e18)]
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
        power = [(extra[f["id"]], f) for f in fs
                 if extra.get(f["id"], {}).get("power") and current(f, extra[f["id"]], boss_rec)]
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
    # What each role did, per head and fight (every fight with a role split, won or lost; the sums exist only for
    # fights collected since they were added).
    fought = [extra[f["id"]] for f in detailed if extra[f["id"]].get("rsum") and extra[f["id"]].get("dmg")]
    for i, row in enumerate(roles):
        heads = sum(d["roles"][i] for d in fought)
        row.update({key: round(sum(d["rsum"][i][j] for d in fought) / heads) if heads else None
                    for j, key in enumerate(("dmg", "taken", "heal", "boost"))})

    with_power = [(extra[f["id"]], f) for f in window
                  if extra.get(f["id"], {}).get("power") and current(f, extra[f["id"]], boss_rec)]
    margins = []
    basis = strength_basis([d for d, _ in with_power])
    for lo, hi in MARGINS:
        sel = [f for d, f in with_power if d.get("rec") and d.get(basis) and lo <= d[basis] / d["rec"] < hi]
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
                  "margins": margins, "basis": basis,
                  "recent": [{"id": f["id"], "kind": f.get("kind"), "name": f.get("name"), "outcome": f.get("outcome"),
                              "power": d["power"], "gear": d.get("gear"), "rec": d.get("rec") or None,
                              "enraged": d.get("enraged"), "secs": d.get("secs"), **fallen(d)}
                             for d, f in sorted(with_power, key=lambda x: -x[1]["id"])[:30]]},
    }



def guild_fights(fights: list[dict], extra: dict[int, dict], now: float, days: int = 30) -> list[dict]:
    """Per guild, from the fights whose detail page names it: the raids on its treasury (how many it fended off and
    what the treasury lost or won) and the bosses it summoned (how many it beat)."""
    rows: dict[str, dict] = {}
    for f in fights:
        d = extra.get(f["id"], {})
        t = iso_ts(f.get("endedAt"))
        if not d.get("gn") or (t and t < now - days * DAY):
            continue
        row = rows.setdefault(d["gn"], {"guild": d["gn"], "raids": 0, "raid_wins": 0, "raid_known": 0, "lost": 0,
                                        "won": 0, "bosses": 0, "boss_wins": 0})
        win = f.get("outcome") == "VICTORY"
        if f.get("kind") == "RAID":
            row["raids"] += 1
            row["raid_wins"] += win
            if d.get("gc") is not None:
                row["raid_known"] += 1
                row["lost" if d["gc"] < 0 else "won"] += abs(d["gc"])
        elif f.get("kind") == "BOSS" and d.get("by"):
            row["bosses"] += 1
            row["boss_wins"] += win
    return sorted(rows.values(), key=lambda r: (-(r["raids"] + r["bosses"]), r["guild"]))


def spread(xs: list[float]) -> dict | None:
    """Mean, sample standard deviation, variance, coefficient of variation (percent), min, median and max."""
    if not xs:
        return None
    mean_ = statistics.fmean(xs)
    std = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return {"n": len(xs), "mean": round(mean_), "std": round(std, 1), "var": round(std * std),
            "cv": round(100 * std / mean_, 1) if mean_ > 0 else None,
            "min": min(xs), "med": round(statistics.median(xs)), "max": max(xs)}


def payout_rows(fights: list[dict], extra: dict[int, dict], since: float = UPDATE) -> list[dict]:
    """One row per fight since `since` whose report named the silver paid out: the mean per fighter who stood at the
    end and per fighter who fell (a fight's digest `pay`). Sums over fighters only, nothing per player."""
    rows = []
    for f in fights:
        pay = extra.get(f["id"], {}).get("pay")
        t = iso_ts(f.get("endedAt"))
        if not pay or not t or t < since or (pay[0] is None and pay[1] is None):
            continue
        rows.append({"id": f["id"], "ended": f["endedAt"], "kind": f.get("kind"), "name": f.get("name"),
                     "level": f.get("bossLevel") if f.get("kind") == "BOSS" else
                     f.get("difficulty") if f.get("kind") == "RAID" else None,
                     "outcome": f.get("outcome"), "fighters": f.get("fighters"),
                     "alive": pay[0], "fallen": pay[1], "pg": extra[f["id"]].get("pg")})
    return rows


def loot_rows(fights: list[dict], extra: dict[int, dict]) -> list[dict]:
    """One row per fight with a loot digest (`lt`, kept since 27.10.2026): how many fighters could take part in the
    loot, what dropped per tier, the guaranteed pieces and how many fighters got a drop. Counts only, nothing per
    player."""
    rows = []
    for f in fights:
        lt = extra.get(f["id"], {}).get("lt")
        if not lt or not f.get("endedAt"):
            continue
        rows.append({"id": f["id"], "ended": f["endedAt"], "kind": f.get("kind"), "name": f.get("name"),
                     "level": f.get("bossLevel") if f.get("kind") == "BOSS" else
                     f.get("difficulty") if f.get("kind") == "RAID" else None,
                     "outcome": f.get("outcome"), "fighters": f.get("fighters"), "eligible": lt["el"],
                     "drops": lt["dr"], "items": sum(lt["dr"].values()), "guaranteed": lt["gu"], "winners": lt["wn"]})
    return rows


def loot(rows: list[dict]) -> list[dict]:
    """Per fight type: fights, fighters in the loot, drops (total, per 100 fighters, per fight with spread, per tier),
    the guaranteed pieces and the share of fighters with a drop. Types without any drop in any fight stay in (a rate of
    0 says something too); raids drop nothing and are left out. The most fights first."""
    types: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        if r["kind"] != "RAID":
            types[(r["kind"], r["name"], r["level"])].append(r)
    out = []
    for (kind, name, level), rs in types.items():
        eligible, items = sum(r["eligible"] for r in rs), sum(r["items"] for r in rs)
        tiers: dict[int, int] = defaultdict(int)
        for r in rs:
            for tier, n in r["drops"].items():
                tiers[int(tier) if tier.isdigit() else -1] += n
        out.append({"kind": kind, "name": name, "difficulty": None, "bossLevel": level if kind == "BOSS" else None,
                    "n": len(rs), "wins": sum(r["outcome"] == "VICTORY" for r in rs), "eligible": eligible,
                    "items": items, "per100": round(100 * items / eligible, 2) if eligible else None,
                    "winners": sum(r["winners"] for r in rs), "guaranteed": sum(r["guaranteed"] for r in rs),
                    "per_fight": spread([r["items"] for r in rs]), "tiers": sorted(tiers.items())})
    return sorted(out, key=lambda t: (-t["n"], t["name"] or ""))


def loot_csv(rows: list[dict]) -> str:
    """The loot rows as a CSV with English column names (`tiers` as tier:count pairs joined by semicolons)."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["fight_id", "ended_at", "kind", "name", "level_or_difficulty", "outcome", "fighters", "in_loot",
                "drops", "guaranteed", "fighters_with_drop", "drops_by_tier"])
    for r in rows:
        w.writerow([r["id"], r["ended"], r["kind"], r["name"], "" if r["level"] is None else r["level"],
                    r["outcome"], r["fighters"], r["eligible"], r["items"], r["guaranteed"], r["winners"],
                    ";".join(f"{t}:{n}" for t, n in sorted(r["drops"].items()))])
    return buf.getvalue()


def pooled(groups: list[dict]) -> dict | None:
    """The pay groups of several fights (collect.pay_group) as one: over every fighter, not over the fights' means.
    Mean, sample std, variance, the extremes and the quartiles (read off the histogram, so within one step)."""
    groups = [g for g in groups if g]
    n = sum(g["n"] for g in groups)
    if not n:
        return None
    total, squares = sum(g["s"] for g in groups), sum(g["q"] for g in groups)
    var = max(0.0, (squares - total * total / n) / (n - 1)) if n > 1 else 0.0
    hist: dict[int, int] = defaultdict(int)
    for g in groups:
        for k, c in g["h"].items():
            hist[int(k)] += c

    def quantile(q):
        seen = 0
        for k in sorted(hist):
            seen += hist[k]
            if seen >= q * n:
                break
        return k
    mean_ = total / n
    return {"n": n, "fights": len(groups), "mean": round(mean_), "std": round(math.sqrt(var), 1), "var": round(var),
            "cv": round(100 * math.sqrt(var) / mean_, 1) if mean_ > 0 else None,
            "min": min(g["lo"] for g in groups), "max": max(g["hi"] for g in groups),
            "q1": quantile(0.25), "med": quantile(0.5), "q3": quantile(0.75)}


def payout(rows: list[dict]) -> list[dict]:
    """Per fight type (bosses by name and level, raids by name and difficulty, adventures by name): the spread of the
    silver a fighter standing at the end got, over the fights; also the mean after a win and after a loss, the mean
    of the fallen and the single values (`pts`, for the strip chart). Types without a payout (raids) are left out;
    the most fights first."""
    types: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        types[(r["kind"], r["name"], r["level"])].append(r)
    out = []
    for (kind, name, level), rs in types.items():
        alive = [r["alive"] for r in rs if r["alive"] is not None]
        if not alive:
            continue
        won = [r["alive"] for r in rs if r["alive"] is not None and r["outcome"] == "VICTORY"]
        lost = [r["alive"] for r in rs if r["alive"] is not None and r["outcome"] != "VICTORY"]
        fallen = [r["fallen"] for r in rs if r["fallen"] is not None]
        out.append({"kind": kind, "name": name, "difficulty": level if kind == "RAID" else None,
                    "bossLevel": level if kind == "BOSS" else None, "n": len(rs),
                    "wins": sum(r["outcome"] == "VICTORY" for r in rs),
                    "alive": spread(alive), "fallen": spread(fallen),
                    "all": pooled([(r.get("pg") or {}).get("a") for r in rs]),
                    "all_fallen": pooled([(r.get("pg") or {}).get("d") for r in rs]),
                    "win": round(statistics.fmean(won)) if won else None,
                    "loss": round(statistics.fmean(lost)) if lost else None, "pts": alive})
    return sorted(out, key=lambda t: (-t["n"], t["name"] or ""))


def payout_csv(rows: list[dict]) -> str:
    """The rows as a CSV with English column names, for people who want to work with the numbers themselves."""
    head = ["fight_id", "ended_at", "kind", "name", "level_or_difficulty", "outcome", "fighters",
            "silver_per_survivor", "silver_per_fallen", "survivor_min", "survivor_max"]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(head)
    for r in rows:
        w.writerow([r["id"], r["ended"], r["kind"], r["name"], "" if r["level"] is None else r["level"],
                    r["outcome"], r["fighters"], "" if r["alive"] is None else r["alive"],
                    "" if r["fallen"] is None else r["fallen"],
                    *(((r.get("pg") or {}).get("a") or {}).get(k, "") for k in ("lo", "hi"))])
    return buf.getvalue()


def stat_curves(fights: list[dict], extra: dict[int, dict], now: float, days: int = 30, step: int = 10,
                boss_rec: dict | None = None) -> list[dict]:
    """Per boss (won fights of the last `days`, since 0.27.0 counted by the collector): for each role and stat the
    fighters per `step` of the stat, with the share that fell and the mean of what they did (`sx` of the digests).
    [{boss, fights, roles: {role: {stat: [[from, n, fallen %, mean done], ...]}}}], the strongest boss first (by its
    recommendation in `boss_rec`, bosses it doesn't know last), then most fights."""
    bosses: dict[str, dict] = {}
    for f in fights:
        sx = extra.get(f["id"], {}).get("sx")
        t = iso_ts(f.get("endedAt"))
        if not sx or f.get("kind") != "BOSS" or f.get("outcome") != "VICTORY" or not t or t < now - days * DAY:
            continue
        b = bosses.setdefault(f.get("name"), {"boss": f.get("name"), "fights": 0, "sums": {}})
        b["fights"] += 1
        for role, stats in sx.items():
            for stat, rows in stats.items():
                for lo, (n, fell, done) in rows.items():
                    k = int(lo) // step * step
                    acc = b["sums"].setdefault(role, {}).setdefault(stat, {}).setdefault(k, [0, 0, 0])
                    acc[0] += n
                    acc[1] += fell
                    acc[2] += done
    out = []
    for b in bosses.values():
        roles = {role: {stat: [[k, n, pct(fell, n), round(done / n) if n else None]
                               for k, (n, fell, done) in sorted(rows.items())]
                        for stat, rows in stats.items()} for role, stats in b["sums"].items()}
        out.append({"boss": b["boss"], "fights": b["fights"], "roles": roles})
    return sorted(out, key=lambda r: (-(boss_rec or {}).get(r["boss"], 0), -r["fights"]))


def logistic_fit(xs: list[float], ys: list[int], ridge: float = 0.001, steps: int = 50) -> tuple[float, float]:
    """Intercept and slope of p(win) = 1 / (1 + e^-(a + b x)) by Newton's method, with a little ridge on the slope
    so that fights that split cleanly (all lost below, all won above) still give a finite curve."""
    a = b = 0.0
    for _ in range(steps):
        ga = gb = haa = hab = hbb = 0.0
        for x, y in zip(xs, ys, strict=True):
            p = 1 / (1 + math.exp(-max(-30.0, min(30.0, a + b * x))))
            w = p * (1 - p)
            ga, gb = ga + y - p, gb + (y - p) * x
            haa, hab, hbb = haa + w, hab + w * x, hbb + w * x * x
        gb -= ridge * b
        hbb += ridge
        det = haa * hbb - hab * hab
        if det <= 1e-12:
            break
        da, db = (hbb * ga - hab * gb) / det, (haa * gb - hab * ga) / det
        a, b = a + da, b + db
        if abs(da) + abs(db) < 1e-9:
            break
    return a, b


def win_odds(fights: list[dict], extra: dict[int, dict], now: float, days: int = 30,
             boss_rec: dict | None = None) -> dict:
    """Boss fights of the last `days` whose live view gave the group's strength and the recommendation (the game's
    group gear once enough fights have it, else the average Kampfkraft, see `strength_basis`; `basis` says which):
    each as [strength / recommendation, won, boss], and a logistic curve through them ([[ratio, win %], ...]) with
    the ratio at which it crosses 50 % (`mid`). Few fights or one outcome only: no curve."""
    seen = []
    for f in fights:
        d, t = extra.get(f["id"], {}), iso_ts(f.get("endedAt"))
        if f.get("kind") == "BOSS" and d.get("power") and d.get("rec") and t and t >= now - days * DAY \
                and current(f, d, boss_rec):
            seen.append((f, d))
    basis = strength_basis([d for _, d in seen])
    points = [[round(d[basis] / d["rec"], 3), int(f.get("outcome") == "VICTORY"), f.get("name")]
              for f, d in seen if d.get(basis)]
    out: dict = {"n": len(points), "points": points, "fit": [], "mid": None, "basis": basis}
    if len(points) < 8 or len({p[1] for p in points}) < 2:
        return out
    a, b = logistic_fit([p[0] for p in points], [p[1] for p in points])
    lo, hi = min(p[0] for p in points), max(p[0] for p in points)
    pad = (hi - lo) * 0.08 or 0.05
    xs = [lo - pad + (hi - lo + 2 * pad) * i / 40 for i in range(41)]
    out["fit"] = [[round(x, 3), round(100 / (1 + math.exp(-max(-30.0, min(30.0, a + b * x)))), 1)] for x in xs]
    out["mid"] = round(-a / b, 3) if b > 0 and lo - pad <= -a / b <= hi + pad else None
    return out
