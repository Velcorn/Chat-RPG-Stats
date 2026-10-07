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

1. `PYTHONPATH=src uv run python -m unittest discover tests` and `uv run ruff check` (the commit hook runs both; CI runs the same hooks plus coverage).
2. Keep the docs current in the same commit, so they never lag the code: README.md (short; what it shows, the request
   table, schedule, setup and commands must be true today), docs/funktionsweise.md (data flow and every calculation)
   and this file's map and facts. Grep them for every number, name and behaviour the change touches, removed things
   included. Operator details (timers, workflow plumbing) belong in docs/funktionsweise.md and this file, not the README.
3. If visitors of the page notice it: bump the version in `pyproject.toml`, `uv lock`, add a German `CHANGELOG.md` entry.
   The changelog lists only what affects users (page, data, addresses); no CI, tests, docs, badges, refactors or
   infrastructure. Changes nobody sees get no entry and no version bump. No git tags.
4. Commit, push: `SSH_AUTH_SOCK=$XDG_RUNTIME_DIR/ssh-agent.socket git push`.

## Project map

Python modules live in `src/` (flat, no package; tests and tools need `PYTHONPATH=src`); `site/`, `tests/`, `docs/` stay at the top.

- `src/collect.py`: one run (about 15 requests plus one per new fight): `snapshot` (the requests), `state_from` (flat current state, incl. the watchlist's gear per slot), `record` (only the changes).
  Writes `data/days/YYYY-MM-DD.jsonl` (one line per run) and `data/state.json` on the `data` branch.
- `src/fightstats.py`: fight statistics for `summary.json` -> `stats` (death share in won fights and per fight (`fallen`), roles, power vs recommendation, hours, channels); only sums per fight, never per player.
- `src/build.py`: replays the day files (`History`, incl. rules log and live share per channel), computes pace, forecasts, peers, guild standing, fight odds; writes
  `_site/data/summary.json`, `players.json` (search index) and `p/<login>.json`.
- `site/index.html`: the whole dashboard (no build step; hash routes `#/<section>/<sub>` with sections `start` (default), `rangliste`, `gilden` (subs `vergleich` + one per guild), `spiel` (subs `wirtschaft`, `regeln`, `aenderungen`; `RULE_LABELS` holds the German rule names), `kaempfe` (subs `arten`, `ueberleben`, `kraft`, `zeit`, `letzte`; see `SECTIONS`: each sub
  page is a tab in the second row) and `#/spieler/<login>`).
- `src/watchlist.py` + `watchlist.txt`: the list (channel owners by default, others opt-in), changed by the issue form via `.github/workflows/watchlist.yml`.
- Fight stories (adventures since 04.10.2026): `collect.story_digest` parses the fight log (`Szene i/n`, `Der Chat wählt ...`) into name-free scenes, `fightstats.story_stats` aggregates them; `fightstats.UPDATE` splits `eras.after`/`eras.before` for the fight pages.
- `tests/`: `test_collect.py`, `test_pipeline.py` (build), `test_fightstats.py`, `test_watchlist.py`, `test_site.py` (the page script parses with `node --check`).
- `docs/funktionsweise.md`: German detail: data flow, storage, watchlist, every calculation. README stays short.
- `.pre-commit-config.yaml` (prek: ruff, tests, hygiene, plain punctuation), `.github/workflows/ci.yml` (hooks + coverage; writes
  the coverage badge with `.github/badge.py` to the `badges` branch, don't commit there), `.github/dependabot.yml`.
- `.github/workflows/collect.yml` (name `collect`): schedule (4-22 UTC, collect.py skips outside 7-24 Berlin), data branch, Pages deploy.
  GitHub's schedule fired once a day on 30.09.2026, so `deploy/chat-rpg-stats-collect.{service,timer}` (systemd user timer
  on the operator's machine) dispatches the workflow every 15 minutes, 7-24 Berlin time.

## Game API facts

- Public without login: `/api/rules`, `/api/leaderboard?by=gear|quests&limit=100` (max 100; `silver` and `level` return
  the gear board), `/api/players/{login}`, `/api/guilds`, `/api/guilds/{login}` (all members with gear score and
  donations), `/api/combat/history` (last 20 fights, about a day), `/api/combat/history/{id}` (one fight: fighters with role and alive, `crowd.tally`, `guildName`/`summonedBy`/`guildOnly`/`treasuryChange` kept as `gn`/`by`/`go`/`gc` in the digest; `power`, `gearScore`, `averagePower`, `recommendedGear` are 0 there), `/api/combat?kompakt=true` (the fight the site still shows: average gear and power, recommendation, `battle`), `/api/channels` (with `chatMode`), `/api/rules`, `/api/compendium` (once a day: tiers, six bosses, fights, projects, `workshop` (Schmiede levels, Lager wares), no more potions; trimmed by `collect.compendium_state`, stored in `state.json` as `compendium`), `/api/guilds/first-kills` (once a day, `collect.first_kills_state`), the game's changelog (a JS literal in the `/changelog` page's script chunk, found via the entry script's router; `collect.read_changelog`, once a day, written by the build as `changelog.json`) (the trader endpoint is not used). The guild page also has `buildings` (WERKSTATT labelled Schmiede, KONTOR, KRIEGSKASSE, WALL, LAGER) [{key, level, maxLevel, effect, nextPrice, nextEffect, blocker}] and `boss.bosses` [{name, highestWon, nextPriceSilver, nextRecommendedGear}], kept per guild in the state (`guild_state`).
  `/api/market/board` needs a login (not used).
- The leaderboard lags the guild pages by a few minutes.
- Since 30.09.2026 `gearScore` (boards, guild pages, guild total) is shown as Kampfkraft, the game's own name for it (a plain ATK+DEF+SUP sum since 04.10.2026).
- Play window 7-24 Berlin time; nothing changes at night.
