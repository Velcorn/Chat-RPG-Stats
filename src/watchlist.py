"""Apply a watchlist issue (form: action + Twitch name) to watchlist.txt. Prints GitHub Actions outputs.

The issue body is untrusted input: only a valid Twitch login gets through, and it must exist in the game.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
from pathlib import Path

import collect

LIST = Path("watchlist.txt")
MAX = 150  # every entry costs one request per run
LOGIN = re.compile(r"^[a-z0-9_]{3,25}$")


def field(body: str, label: str) -> str:
    m = re.search(rf"### {re.escape(label)}\s*\n+(.+)", body)
    return m.group(1).strip() if m else ""


def apply(body: str, path: Path = LIST, exists=None) -> tuple[bool, str, str]:
    """(changed, summary for the commit, German reply)."""
    login = field(body, "Twitch-Name").lower().lstrip("@").strip()
    remove = field(body, "Was soll passieren?") == "Entfernen"
    if not LOGIN.match(login):
        return False, "", "Das sieht nicht nach einem Twitch-Namen aus (3 bis 25 Zeichen: Buchstaben, Ziffern, _)."
    names = collect.read_watchlist(path)
    above, below = collect.manual_lines(path.read_text("utf-8")) if path.exists() else ([], None)
    if remove:
        if login not in names:
            if login in (below or []):
                return False, "", (f"{login} steht nur als Spieler der Top 100 auf der Liste; diesen Teil pflegt die "
                                   "Seite selbst.")
            return False, "", f"{login} steht nicht auf der Liste."
        above = [ln for ln in above if ln.split("#")[0].strip().lower() != login]
        write(path, above, below)
        return True, f"remove {login}", f"{login} ist von der Liste entfernt. Die bisher gesammelten Daten bleiben."
    if login in names:
        return False, "", f"{login} steht schon auf der Liste."
    if len(names) >= MAX:
        return False, "", "Die Liste ist voll. Das hält die Anfragen an die Seite klein, sorry."
    if not (exists or player_exists)(login):
        return False, "", f"{login} gibt es im Spiel nicht (oder die Seite war gerade nicht erreichbar)."
    write(path, [*above, login], below)
    return True, f"add {login}", (f"{login} steht jetzt auf der Liste. Die ersten Daten kommen mit dem nächsten Lauf "
                                  "(höchstens 5 Minuten).")


def write(path: Path, above: list[str], below: list[str] | None) -> None:
    """The file: the lines by hand, then (if it has an automatic part) its marker and the top 100."""
    lines = above if below is None else [*above, collect.AUTO_MARK, *below]
    path.write_text("\n".join(lines) + "\n", "utf-8")


def sync(top: list[str], path: Path = LIST) -> bool:
    """Make the automatic part the board's top 100 (those not already listed above it), in board order. The part
    above the marker, the channel owners and every entry added by the issue form, is never touched."""
    text = path.read_text("utf-8") if path.exists() else ""
    above, _ = collect.manual_lines(text)
    mine = set(collect.read_watchlist(path))
    below = [login for login in top if login not in mine]
    new = "\n".join([*above, collect.AUTO_MARK, *below]) + "\n"
    if new == text:
        return False
    path.write_text(new, "utf-8")
    return True


def player_exists(login: str) -> bool:
    try:
        return bool(collect.Site().get(f"/api/players/{login}"))
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--sync":  # the collect workflow, after a run: state.json -> the top 100
        board = json.loads(Path(sys.argv[2]).read_text("utf-8")).get("boards", {}).get("gear", [])
        print(f"changed={'true' if sync([login.lower() for login, _ in board[:collect.TOP_WATCH]], LIST) else 'false'}")
        return 0
    changed, summary, message = apply(os.environ.get("BODY", ""))
    print(f"changed={'true' if changed else 'false'}")
    print(f"summary={summary}")
    print(f"message={message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
