"""Apply a watchlist issue (form: action + Twitch name) to watchlist.txt. Prints GitHub Actions outputs.

The issue body is untrusted input: only a valid Twitch login gets through, and it must exist in the game.
"""
from __future__ import annotations

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
    if remove:
        if login not in names:
            return False, "", f"{login} steht nicht auf der Liste."
        lines = [ln for ln in path.read_text("utf-8").splitlines() if ln.split("#")[0].strip().lower() != login]
        path.write_text("\n".join(lines) + "\n", "utf-8")
        return True, f"remove {login}", f"{login} ist von der Liste entfernt. Die bisher gesammelten Daten bleiben."
    if login in names:
        return False, "", f"{login} steht schon auf der Liste."
    if len(names) >= MAX:
        return False, "", "Die Liste ist voll. Das hält die Anfragen an die Seite klein, sorry."
    if not (exists or player_exists)(login):
        return False, "", f"{login} gibt es im Spiel nicht (oder die Seite war gerade nicht erreichbar)."
    with path.open("a", encoding="utf-8") as fh:
        fh.write(login + "\n")
    return True, f"add {login}", (f"{login} steht jetzt auf der Liste. Die ersten Daten kommen mit dem nächsten Lauf "
                                  "(höchstens 15 Minuten, nachts erst ab 7 Uhr).")


def player_exists(login: str) -> bool:
    try:
        return bool(collect.Site().get(f"/api/players/{login}"))
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


def main() -> int:
    changed, summary, message = apply(os.environ.get("BODY", ""))
    print(f"changed={'true' if changed else 'false'}")
    print(f"summary={summary}")
    print(f"message={message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
