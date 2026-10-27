"""One-off catch-up: the pay spread (`pg`) and loot counts (`lt`) of fights collected before the collector kept them.

The game keeps a fight's report for a week. This reads those reports again, a request every PAUSE seconds like a
normal run, and writes the two digests into a day file of its own (`<day>-backfill.jsonl`, a record that only carries
`fightx`; `build.History` merges it and does not count it as a run). Counts and spreads only, nothing per player."""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
from datetime import datetime
from pathlib import Path

import build
import collect
import fightstats

KEPT = 6.5 * 86400  # a bit under the game's week, so a report is not deleted while it is read


def missing(h: build.History, now: float) -> list[dict]:
    """Fights of the last days (not raids: they drop and pay nothing) that have no loot digest yet, oldest first."""
    out = [f for f in h.fights if f.get("kind") != "RAID" and "lt" not in h.fightx.get(f["id"], {})
           and (t := fightstats.iso_ts(f.get("endedAt"))) and t >= now - KEPT]
    return sorted(out, key=lambda f: f["id"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--limit", type=int, default=150, help="most reports to read")
    ap.add_argument("--dry", action="store_true", help="only count what is missing")
    args = ap.parse_args()
    now = time.time()
    todo = missing(build.History(build.replay(args.data / "days")), now)[:args.limit]
    print(f"{len(todo)} Kämpfe ohne Beute- und Silberverteilung")
    if args.dry or not todo:
        return 0
    site, got = collect.Site(), {}
    for f in todo:
        try:
            digest = collect.detail_digest(site.get(f"/api/combat/history/{f['id']}"))
        except urllib.error.HTTPError as exc:
            print(f"Kampf {f['id']}: {exc.code}, übersprungen")
            continue
        got[str(f["id"])] = {k: digest[k] for k in ("pg", "lt")}
    path = args.data / "days" / f"{datetime.fromtimestamp(now):%Y-%m-%d}-backfill.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"t": int(now), "part": "backfill", "req": site.requests, "fightx": got},
                            ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"{len(got)} Kämpfe nachgetragen, {site.requests} Anfragen -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
