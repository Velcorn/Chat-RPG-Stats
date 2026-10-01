# CLAUDE.md

Public, read-only stats dashboard for the Twitch chat RPG at rpg.sola.rip. A GitHub Action collects public data every
15 minutes and publishes a static page on GitHub Pages. See README.md (German) for what it shows and how it calculates.

## Principles

- **Read-only, public data only.** No login, no cookies, never anything but GETs. Nothing automated in the game or chat.
- **Keep requests low.** One collector for everyone; visitors only read the published files. Don't add endpoints or
  per-player requests without need; the watchlist is capped (opt-in for players; the channel owners are on it by default). The site's operator can ask us to stop at any time.
- **No activity logs per player.** Store values and their changes (gear, silver, stat totals), never a player's
  individual quests or fights with times and channels: that would show when and where someone plays.
- The README's request table must match what `collect.snapshot` actually does.
- **Never mention the operator's other projects or accounts** anywhere (README, docs, page, changelog, comments, commit
  messages). This project stands on its own.

## How to work (Karpathy's guidelines)

1. **Think before coding.** State assumptions; if a request is ambiguous, ask. Check facts against the code and the
   live API (read-only GETs, sparingly).
2. **Simplicity first.** The least code that solves the problem. No speculative features.
3. **Surgical changes.** Touch only what the task needs; match the surrounding style.
4. **Goal-driven execution.** Turn the task into a checkable goal and verify it. For page changes, build and look at
   the page (desktop and phone width).

## Language

Everything users see is German (README, page, issue form, Action replies); code, comments and commits stay
English. Exception: badge labels and the names of workflows that show up in a badge are English (`coverage`, `collect`). Amounts in silver with the German thousands separator (`fmtSilver`), numbers with nouns via `count`. Plain
punctuation: `-` instead of dashes, `...` instead of the ellipsis character, `->` instead of arrows, straight quotes. The README and the page footer carry the vibe-coding notice (mostly AI-written, spot-checked);
keep it.

## After every change

1. `uv run python -m unittest discover tests` and `uv run ruff check` (the commit hook runs both; CI runs the same hooks plus coverage).
2. Keep the docs current in the same commit, so they never lag the code: README.md (short; what it shows, the request
   table, schedule, setup and commands must be true today), docs/funktionsweise.md (data flow and every calculation)
   and this file's map and facts. Grep them for every number, name and behaviour the change touches, removed things
   included. Operator details (timers, workflow plumbing) belong in docs/funktionsweise.md and this file, not the README.
3. If visitors of the page notice it: bump the version in `pyproject.toml`, `uv lock`, add a German `CHANGELOG.md` entry.
   The changelog lists only what affects users (page, data, addresses); no CI, tests, docs, badges, refactors or
   infrastructure. Changes nobody sees get no entry and no version bump. No git tags.
4. Commit, push: `SSH_AUTH_SOCK=$XDG_RUNTIME_DIR/ssh-agent.socket git push`.

## Project map

- `collect.py`: one run: `snapshot` (the requests), `state_from` (flat current state, incl. the watchlist's gear per slot), `record` (only the changes).
  Writes `data/days/YYYY-MM-DD.jsonl` (one line per run) and `data/state.json` on the `data` branch.
- `build.py`: replays the day files (`History`), computes pace, forecasts, peers, guild standing, fight odds; writes
  `_site/data/summary.json`, `players.json` (search index) and `p/<login>.json`.
- `site/index.html`: the whole dashboard (no build step; hash routes `#/<section>/<sub>` with sections `start` (default), `rangliste`, `gilden`, `kaempfe` (see `SECTIONS`: each sub
  page is a tab in the second row) and `#/spieler/<login>`).
- `watchlist.py` + `watchlist.txt`: the list (channel owners by default, others opt-in), changed by the issue form via `.github/workflows/watchlist.yml`.
- `tests/`: `test_collect.py`, `test_pipeline.py` (build), `test_watchlist.py`.
- `docs/funktionsweise.md`: German detail: data flow, storage, watchlist, every calculation. README stays short.
- `.pre-commit-config.yaml` (prek: ruff, tests, hygiene, plain punctuation), `.github/workflows/ci.yml` (hooks + coverage; writes
  the coverage badge with `.github/badge.py` to the `badges` branch, don't commit there), `.github/dependabot.yml`.
- `.github/workflows/collect.yml` (name `collect`): schedule (4-22 UTC, collect.py skips outside 7-24 Berlin), data branch, Pages deploy.
  GitHub's schedule fired once a day on 30.09.2026, so `deploy/chat-rpg-stats-collect.{service,timer}` (systemd user timer
  on the operator's machine) dispatches the workflow every 15 minutes, 7-24 Berlin time.

## Game API facts

- Public without login: `/api/rules`, `/api/leaderboard?by=gear|quests&limit=100` (max 100; `silver` and `level` return
  the gear board), `/api/players/{login}`, `/api/guilds`, `/api/guilds/{login}` (all members with gear score and
  donations), `/api/combat/history` (last 20 fights, about a day), `/api/trader`, `/api/channels`.
  `/api/market/board` needs a login (not used).
- The leaderboard lags the guild pages by a few minutes.
- Since 30.09.2026 `gearScore` (boards, guild pages, guild total) is Kampfkraft: gear (ATK+DEF+SUP) plus a talent bonus the API
  doesn't show. The page calls it Kampfkraft; the estimated bonus formula on `#/rangliste/formel` is hand-written text (update it
  when the fit changes).
- Play window 7-24 Berlin time; nothing changes at night.
