"""Freeze the generated public dashboard data for one completed season.

Run this against a checkout of the data branch immediately after the season's final collection. The raw day files
stay untouched; the generated files are copied below data/seasons/<id> and are served as an immutable dashboard.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

import build

ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def write_atomic(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), "utf-8")
    os.replace(tmp, path)


def archive(data: Path, season_id: str, label: str, end: int | None = None) -> dict:
    """Build and store an immutable public snapshot; refuse to replace an existing archive."""
    if not ID.fullmatch(season_id):
        raise ValueError("season id must contain lowercase letters, numbers and single hyphens")
    if not label.strip():
        raise ValueError("season label must not be empty")
    destination = data / "seasons" / season_id
    if destination.exists():
        raise FileExistsError(f"season already archived: {season_id}")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        summary = build.build(data, out, now=end, include_archives=False)
        season = {"id": season_id, "label": label, "start": summary.get("since"),
                  "end": summary["generated"], "archived": True}
        summary["season"] = season
        build.write(out / "data" / "summary.json", summary)
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = destination.parent / f".{season_id}.tmp"
        shutil.rmtree(staging, ignore_errors=True)
        shutil.copytree(out / "data", staging)
        (staging / "seasons.json").unlink(missing_ok=True)
        os.replace(staging, destination)
    manifest = build.season_manifest(data)
    archives = [entry for entry in manifest["archives"] if entry.get("id") != season_id]
    manifest["archives"] = sorted([*archives, season], key=lambda entry: entry.get("end") or 0, reverse=True)
    write_atomic(data / "seasons.json", manifest)
    return season


def main() -> None:
    ap = argparse.ArgumentParser(description="Eine abgeschlossene Saison unveränderlich archivieren")
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--id", required=True, help="z. B. beta-2026")
    ap.add_argument("--label", required=True, help="z. B. Beta 2026")
    ap.add_argument("--end", type=int, help="Unix-Zeit; Vorgabe ist der letzte gesammelte Stand")
    args = ap.parse_args()
    season = archive(args.data, args.id, args.label, args.end)
    print(f"{season['label']} archiviert: {season['start']} bis {season['end']}")


if __name__ == "__main__":
    main()
